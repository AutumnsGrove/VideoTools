package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"

	lipgloss "charm.land/lipgloss/v2"
)

// -------- Configuration --------

type transcriptionConfig struct {
	PromptAfterCompress bool   `json:"prompt_after_compress"`
	ParakeetModel       string `json:"parakeet_model"`
	JournalBaseDir      string `json:"journal_base_dir"`
	AnthropicModel      string `json:"anthropic_model"`
	EnhanceWithLLM      bool   `json:"enhance_with_llm"`
	EnhancementPrompt   string `json:"enhancement_prompt"`
	SecretsPath         string `json:"secrets_path"`
	TempDir             string `json:"temp_dir"`
}

const defaultEnhancementPrompt = `You are an expert transcript editor. Your task is to enhance a raw transcript while preserving authenticity.

## Pre-Processing Check
First, determine if the transcript should be processed:
- If less than 50 meaningful words, return only: SKIP: Too short
- If mostly silence/non-verbal, return only: SKIP: No meaningful content
- If corrupted/incoherent, return only: SKIP: Corrupted transcript

## Processing Rules

1. **Preserve ALL original words** (except filler removal)
2. **Add structure and formatting:**
   - Insert paragraph breaks between distinct thoughts
   - Add topic headers: ### *Topic: [Name]*
   - Add "circling back" headers: ### *Circling Back: [Name]*
   - Add brief context notes: ***[context: description]*** (max 10 words)

3. **Remove only:**
   - Filler words: um, uh, like (unless meaningful)
   - Fix obvious transcription errors

4. **Never:**
   - Summarize or condense
   - Rewrite for style
   - Remove repetitions or tangents

## Output
Return the enhanced transcript with all formatting applied. Assume single speaker unless absolutely clear otherwise.

Remember: Be conservative with changes. When in doubt, preserve the original.`

const titlePrompt = `Generate a brief, descriptive title for this transcript. Requirements:
- Maximum 10 words
- Capture the main topic or theme
- Be specific and informative
- No quotation marks or special formatting
- Just return the title, nothing else

Transcript excerpt:`

// -------- Secrets loading --------

func loadSecrets(paths ...string) map[string]string {
	for _, p := range paths {
		if p == "" {
			continue
		}
		data, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		var secrets map[string]string
		if err := json.Unmarshal(data, &secrets); err != nil {
			continue
		}
		return secrets
	}
	return nil
}

// resolveAPIKey tries config secrets path, common locations, then env var.
func resolveAPIKey(cfg config) string {
	candidates := []string{cfg.Transcription.SecretsPath}

	// Check common secrets.json locations.
	if home, err := os.UserHomeDir(); err == nil {
		candidates = append(candidates,
			filepath.Join(home, "Documents", "Audiotools", "secrets.json"),
			filepath.Join(home, ".config", "camera-sync", "secrets.json"),
		)
	}
	candidates = append(candidates, "secrets.json")

	secrets := loadSecrets(candidates...)
	if key, ok := secrets["anthropic_api_key"]; ok && key != "" {
		return key
	}

	// Fallback to environment variable.
	return os.Getenv("ANTHROPIC_API_KEY")
}

// -------- Recording time extraction --------

// getRecordingTime extracts the creation_time from video metadata via ffprobe,
// falling back to file modification time.
func getRecordingTime(path string) time.Time {
	cmd := exec.Command("ffprobe",
		"-v", "quiet",
		"-select_streams", "v:0",
		"-show_entries", "stream_tags=creation_time:format_tags=creation_time",
		"-of", "csv=p=0",
		path,
	)
	out, err := cmd.Output()
	if err == nil {
		raw := strings.TrimSpace(string(out))
		if lines := strings.Split(raw, "\n"); len(lines) > 0 {
			line := strings.TrimSpace(lines[0])
			if line != "" && line != "N/A" {
				for _, fmt := range []string{
					"2006-01-02T15:04:05.000000Z",
					"2006-01-02T15:04:05Z",
					"2006-01-02 15:04:05",
				} {
					if t, err := time.Parse(fmt, line); err == nil {
						return t.Local()
					}
				}
			}
		}
	}

	// Fallback to file mtime.
	if info, err := os.Stat(path); err == nil {
		return info.ModTime()
	}
	return time.Now()
}

// -------- Audio extraction --------

func extractAudio(ctx context.Context, videoPath, tempDir string) (string, error) {
	stem := strings.TrimSuffix(filepath.Base(videoPath), filepath.Ext(videoPath))
	mp3Path := filepath.Join(tempDir, stem+".mp3")

	args := []string{
		"-y", "-i", videoPath,
		"-q:a", "0",
		"-map", "a",
		mp3Path,
	}
	cmd := exec.CommandContext(ctx, "ffmpeg", args...)
	var stderr bytes.Buffer
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("audio extraction: %w: %s", err, lastLines(stderr.String(), 3))
	}
	return mp3Path, nil
}

// -------- Parakeet transcription --------

func transcribeWithParakeet(ctx context.Context, mp3Path, model, tempDir string) (string, error) {
	args := []string{
		"--output-format", "txt",
		"--output-dir", tempDir,
	}
	if model != "" {
		args = append(args, "--model", model)
	}
	args = append(args, mp3Path)

	cmd := exec.CommandContext(ctx, "parakeet-mlx", args...)
	var stderr bytes.Buffer
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("parakeet-mlx: %w: %s", err, lastLines(stderr.String(), 3))
	}

	stem := strings.TrimSuffix(filepath.Base(mp3Path), ".mp3")
	txtPath := filepath.Join(tempDir, stem+".txt")
	data, err := os.ReadFile(txtPath)
	if err != nil {
		return "", fmt.Errorf("reading transcript: %w", err)
	}
	os.Remove(txtPath)
	return strings.TrimSpace(string(data)), nil
}

// -------- Anthropic API --------

type anthropicMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type anthropicSystemBlock struct {
	Type         string                 `json:"type"`
	Text         string                 `json:"text"`
	CacheControl map[string]string      `json:"cache_control,omitempty"`
}

type anthropicRequest struct {
	Model       string                 `json:"model"`
	MaxTokens   int                    `json:"max_tokens"`
	Temperature float64                `json:"temperature"`
	System      []anthropicSystemBlock `json:"system,omitempty"`
	Messages    []anthropicMessage     `json:"messages"`
}

type anthropicResponse struct {
	Content []struct {
		Text string `json:"text"`
	} `json:"content"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error"`
}

func callAnthropic(apiKey, model string, maxTokens int, temperature float64, systemPrompt, userContent string) (string, error) {
	reqBody := anthropicRequest{
		Model:       model,
		MaxTokens:   maxTokens,
		Temperature: temperature,
		System: []anthropicSystemBlock{
			{
				Type:         "text",
				Text:         systemPrompt,
				CacheControl: map[string]string{"type": "ephemeral"},
			},
		},
		Messages: []anthropicMessage{
			{Role: "user", Content: userContent},
		},
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", "https://api.anthropic.com/v1/messages", bytes.NewReader(jsonData))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("API request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("reading response: %w", err)
	}

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("API error %d: %s", resp.StatusCode, string(body))
	}

	var result anthropicResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return "", fmt.Errorf("parse response: %w", err)
	}
	if result.Error != nil {
		return "", fmt.Errorf("API error: %s", result.Error.Message)
	}
	if len(result.Content) == 0 {
		return "", fmt.Errorf("empty response from API")
	}
	return strings.TrimSpace(result.Content[0].Text), nil
}

func generateTitle(apiKey, model, transcript string) (string, error) {
	// Use first 1000 chars for title generation.
	excerpt := transcript
	if len(excerpt) > 1000 {
		excerpt = excerpt[:1000]
	}

	title, err := callAnthropic(apiKey, model, 20, 0.65, titlePrompt,
		"Generate a title for this transcript excerpt:\n\n"+excerpt)
	if err != nil {
		return "", err
	}

	// Clean: remove special chars, limit to 8 words.
	var cleaned []string
	for _, word := range strings.Fields(title) {
		w := strings.Map(func(r rune) rune {
			if r == '-' || (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == ' ' {
				return r
			}
			return -1
		}, word)
		if w != "" {
			cleaned = append(cleaned, w)
		}
		if len(cleaned) >= 8 {
			break
		}
	}
	if len(cleaned) == 0 {
		return "Video Transcript", nil
	}
	return strings.Join(cleaned, " "), nil
}

func enhanceTranscript(apiKey, model, prompt, transcript string) (string, error) {
	// Check if transcript is too short.
	if len(strings.Fields(transcript)) < 10 {
		return transcript, nil
	}

	enhanced, err := callAnthropic(apiKey, model, 8000, 0.6, prompt,
		"Please enhance this transcript:\n\n"+transcript)
	if err != nil {
		return "", err
	}

	// If LLM returned a SKIP response, return original.
	if strings.HasPrefix(strings.TrimSpace(enhanced), "SKIP:") {
		return transcript, nil
	}
	return enhanced, nil
}

// -------- Journal writing --------

// getJournalDir returns the journal directory for a given year.
func getJournalDir(baseDir string, year int) string {
	return filepath.Join(baseDir, fmt.Sprintf("%d Auto", year))
}

// getTranscribedVideoNames scans all journal auto directories for already-transcribed
// video names, returning a set of stems.
func getTranscribedVideoNames(baseDir string) map[string]bool {
	transcribed := make(map[string]bool)
	pattern := filepath.Join(baseDir, "* Auto", "*-auto.md")
	matches, _ := filepath.Glob(pattern)
	for _, path := range matches {
		f, err := os.Open(path)
		if err != nil {
			continue
		}
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.HasPrefix(line, "### Video: ") {
				name := strings.TrimPrefix(line, "### Video: ")
				transcribed[strings.TrimSpace(name)] = true
			}
		}
		f.Close()
	}
	return transcribed
}

func writeJournalEntry(baseDir, videoName string, recordingTime time.Time, transcript, title string) (string, error) {
	year := recordingTime.Year()
	journalDir := getJournalDir(baseDir, year)
	if err := os.MkdirAll(journalDir, 0755); err != nil {
		return "", fmt.Errorf("create journal dir: %w", err)
	}

	dateStr := recordingTime.Format("2006-01-02")
	timeStr := recordingTime.Format("15:04:05")
	journalPath := filepath.Join(journalDir, dateStr+"-auto.md")

	displayTitle := title
	if displayTitle == "" {
		displayTitle = videoName
	}

	// Create file with header if new.
	if _, err := os.Stat(journalPath); os.IsNotExist(err) {
		header := fmt.Sprintf("# Daily Auto Journal - %s\n\n", recordingTime.Format("January 02, 2006"))
		if err := os.WriteFile(journalPath, []byte(header), 0644); err != nil {
			return "", fmt.Errorf("create journal file: %w", err)
		}
	}

	entry := fmt.Sprintf("## %s (%s %s)\n### Video: %s\n\n%s\n\n---\n\n",
		displayTitle, dateStr, timeStr, videoName, transcript)

	f, err := os.OpenFile(journalPath, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return "", fmt.Errorf("open journal: %w", err)
	}
	defer f.Close()
	if _, err := f.WriteString(entry); err != nil {
		return "", fmt.Errorf("write journal entry: %w", err)
	}
	return journalPath, nil
}

// -------- Per-file transcription --------

type transcribeResult struct {
	path        string
	journalPath string
	title       string
	err         error
	stage       string
}

func transcribeOne(ctx context.Context, cfg config, apiKey, path string, idx, total int) transcribeResult {
	filename := filepath.Base(path)
	stem := strings.TrimSuffix(filename, filepath.Ext(filename))
	tempDir := cfg.Transcription.TempDir
	os.MkdirAll(tempDir, 0755)

	printTranscribeStep := func(step string) {
		compressMu.Lock()
		defer compressMu.Unlock()
		fmt.Print("\r\033[K")
		lipgloss.Println(timestamp() + " " + transcribeStyle.Render("TRANSCRIBE") + " " +
			dimStyle.Render(fmt.Sprintf("[%d/%d]", idx, total)) + " " +
			valueStyle.Render(filename) + " " +
			dimStyle.Render("· "+step))
	}

	// Pre-flight: verify the video file is valid before any processing.
	printTranscribeStep("validating file")
	if fi, err := os.Stat(path); err != nil {
		return transcribeResult{path: path, err: fmt.Errorf("cannot access file: %w", err), stage: "validate"}
	} else if fi.Size() == 0 {
		return transcribeResult{path: path, err: fmt.Errorf("file is 0 bytes (empty/corrupt recording)"), stage: "validate"}
	}
	// Quick ffprobe check to ensure the container is readable.
	probeCmd := exec.CommandContext(ctx, "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path)
	if probeOut, err := probeCmd.CombinedOutput(); err != nil {
		detail := strings.TrimSpace(string(probeOut))
		if detail == "" {
			detail = err.Error()
		}
		return transcribeResult{path: path, err: fmt.Errorf("file is not a valid video: %s", detail), stage: "validate"}
	}

	// Step 1: Extract audio.
	printTranscribeStep("extracting audio")
	mp3Path, err := extractAudio(ctx, path, tempDir)
	if err != nil {
		return transcribeResult{path: path, err: err, stage: "audio"}
	}
	defer os.Remove(mp3Path)

	// Step 2: Transcribe with parakeet.
	printTranscribeStep("transcribing with parakeet")
	transcript, err := transcribeWithParakeet(ctx, mp3Path, cfg.Transcription.ParakeetModel, tempDir)
	if err != nil {
		return transcribeResult{path: path, err: err, stage: "transcribe"}
	}

	if strings.TrimSpace(transcript) == "" {
		return transcribeResult{path: path, err: fmt.Errorf("empty transcript"), stage: "transcribe"}
	}

	// Step 3: Enhance with LLM (optional).
	title := ""
	finalTranscript := transcript
	if cfg.Transcription.EnhanceWithLLM && apiKey != "" {
		model := cfg.Transcription.AnthropicModel

		printTranscribeStep("generating title")
		if t, err := generateTitle(apiKey, model, transcript); err == nil {
			title = t
		}

		prompt := cfg.Transcription.EnhancementPrompt
		if prompt == "" {
			prompt = defaultEnhancementPrompt
		}

		printTranscribeStep("enhancing transcript")
		if enhanced, err := enhanceTranscript(apiKey, model, prompt, transcript); err == nil {
			finalTranscript = enhanced
		}
	}

	// Step 4: Write to journal.
	printTranscribeStep("saving to journal")
	recordingTime := getRecordingTime(path)
	journalPath, err := writeJournalEntry(cfg.Transcription.JournalBaseDir, stem, recordingTime, finalTranscript, title)
	if err != nil {
		return transcribeResult{path: path, err: err, stage: "journal"}
	}

	// Done line.
	compressMu.Lock()
	fmt.Print("\r\033[K")
	displayTitle := title
	if displayTitle == "" {
		displayTitle = stem
	}
	lipgloss.Println(timestamp() + " " + copiedStyle.Render("DONE      ") + " " +
		valueStyle.Render(filename) + " " +
		dimStyle.Render("→") + " " +
		dimStyle.Render(displayTitle))
	compressMu.Unlock()

	return transcribeResult{path: path, journalPath: journalPath, title: title}
}

// -------- Top-level transcription runners --------

// runTranscription transcribes a list of video paths.
func runTranscription(ctx context.Context, cfg config, paths []string) error {
	if len(paths) == 0 {
		lipgloss.Println(dimStyle.Render("No videos to transcribe."))
		return nil
	}

	apiKey := resolveAPIKey(cfg)

	lipgloss.Println(labelStyle.Render("  Parakeet:    ") + valueStyle.Render(
		ternaryStr(cfg.Transcription.ParakeetModel != "", cfg.Transcription.ParakeetModel, "(default)")))
	lipgloss.Println(labelStyle.Render("  Journal:     ") + valueStyle.Render(cfg.Transcription.JournalBaseDir))
	lipgloss.Println(labelStyle.Render("  LLM:         ") + valueStyle.Render(
		ternaryStr(cfg.Transcription.EnhanceWithLLM && apiKey != "", cfg.Transcription.AnthropicModel, "disabled")))
	fmt.Println()

	// Sort by recording time (oldest first) so journal entries are chronological.
	type videoWithTime struct {
		path string
		time time.Time
	}
	vts := make([]videoWithTime, len(paths))
	for i, p := range paths {
		vts[i] = videoWithTime{path: p, time: getRecordingTime(p)}
	}
	sort.Slice(vts, func(i, j int) bool {
		return vts[i].time.Before(vts[j].time)
	})

	// Check for already-transcribed videos.
	transcribed := getTranscribedVideoNames(cfg.Transcription.JournalBaseDir)
	var eligible []string
	var skippedCount int
	for _, v := range vts {
		stem := strings.TrimSuffix(filepath.Base(v.path), filepath.Ext(v.path))
		if transcribed[stem] {
			skippedCount++
			continue
		}
		eligible = append(eligible, v.path)
	}
	if skippedCount > 0 {
		lipgloss.Println(dimStyle.Render(fmt.Sprintf("Skipping %d already-transcribed video(s).", skippedCount)))
	}
	if len(eligible) == 0 {
		lipgloss.Println(dimStyle.Render("All videos already transcribed."))
		return nil
	}

	lipgloss.Println(infoStyle.Render(fmt.Sprintf("%d video(s) to transcribe.", len(eligible))))
	fmt.Println()

	start := time.Now()
	var errors []transcribeResult
	var successCount int

	for i, p := range eligible {
		select {
		case <-ctx.Done():
			lipgloss.Println(warnStyle.Render("Transcription cancelled."))
			return nil
		default:
		}

		result := transcribeOne(ctx, cfg, apiKey, p, i+1, len(eligible))
		if result.err != nil {
			errors = append(errors, result)
			compressMu.Lock()
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + errorStyle.Render("FAIL      ") + " " +
				valueStyle.Render(filepath.Base(p)) + " " +
				dimStyle.Render(fmt.Sprintf("[%s]", result.stage)) + " " +
				dimStyle.Render(result.err.Error()))
			compressMu.Unlock()
		} else {
			successCount++
		}
	}

	// Summary.
	fmt.Println()
	divider := dividerStyle.Render(strings.Repeat("━", 50))
	lipgloss.Println(divider)
	elapsed := time.Since(start).Round(time.Second)
	lipgloss.Println(headerStyle.Render("Transcription complete") + " " +
		dimStyle.Render(fmt.Sprintf("in %s", elapsed)))
	fmt.Println()
	lipgloss.Println(labelStyle.Render("  Transcribed: ") + copiedStyle.Render(
		fmt.Sprintf("%d/%d", successCount, len(eligible))))
	if len(errors) > 0 {
		lipgloss.Println(labelStyle.Render("  Failed:      ") + errorStyle.Render(
			fmt.Sprintf("%d", len(errors))))
		for _, e := range errors {
			lipgloss.Println("  " + errorStyle.Render("✗") + " " +
				valueStyle.Render(filepath.Base(e.path)) + " " +
				dimStyle.Render(fmt.Sprintf("[%s] %s", e.stage, e.err.Error())))
		}
	}
	fmt.Println()

	return nil
}

// runTranscribeFile transcribes a single file.
func runTranscribeFile(ctx context.Context, cfg config, path string) error {
	if _, err := os.Stat(path); err != nil {
		return fmt.Errorf("file not found: %w", err)
	}
	return runTranscription(ctx, cfg, []string{path})
}

// runTranscribeDir scans a directory for video files and transcribes them.
func runTranscribeDir(ctx context.Context, cfg config, dir string) error {
	lipgloss.Print(timestamp() + " " + infoStyle.Render("Scanning for video files..."))
	scanStart := time.Now()

	var allVideos []string
	err := filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			if d.Name() != filepath.Base(dir) && strings.HasPrefix(d.Name(), ".") {
				return filepath.SkipDir
			}
			return nil
		}
		if isVideoPath(path) {
			allVideos = append(allVideos, path)
		}
		return nil
	})
	if err != nil {
		return err
	}

	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d video(s)", len(allVideos))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", time.Since(scanStart).Round(time.Millisecond))))

	if len(allVideos) == 0 {
		lipgloss.Println(dimStyle.Render("No video files found."))
		return nil
	}

	fmt.Println()
	return runTranscription(ctx, cfg, allVideos)
}

// -------- Helpers --------

func lastLines(s string, n int) string {
	s = strings.TrimSpace(s)
	lines := strings.Split(s, "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return strings.Join(lines, " | ")
}
