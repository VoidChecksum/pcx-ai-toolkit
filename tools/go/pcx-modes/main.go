package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Registry struct {
	Default string          `json:"default"`
	Modes   map[string]Mode `json:"modes"`
}

type Mode struct {
	ID               string   `json:"id"`
	Name             string   `json:"name"`
	Extensions       []string `json:"extensions"`
	Aliases          []string `json:"aliases"`
	Entrypoint       string   `json:"entrypoint"`
	LLMSPack         string   `json:"llms_pack"`
	Docs             []string `json:"docs"`
	Skills           []string `json:"skills"`
	VerifyCommand    string   `json:"verify_command"`
	ProductionStatus string   `json:"production_status"`
}

func loadRegistry(path string) (Registry, error) {
	body, err := os.ReadFile(path)
	if err != nil {
		return Registry{}, err
	}
	var reg Registry
	if err := json.Unmarshal(body, &reg); err != nil {
		return Registry{}, err
	}
	if len(reg.Modes) == 0 {
		return Registry{}, errors.New("language registry has no modes")
	}
	return reg, nil
}

func normalize(reg Registry, alias string) (string, bool) {
	needle := strings.ToLower(strings.TrimSpace(alias))
	if needle == "" {
		needle = reg.Default
	}
	for id, mode := range reg.Modes {
		if needle == strings.ToLower(id) {
			return id, true
		}
		for _, item := range mode.Aliases {
			if needle == strings.ToLower(item) {
				return id, true
			}
		}
	}
	return "", false
}

func registryPath() string {
	if path := os.Getenv("PCX_LANGUAGE_MODES"); path != "" {
		return path
	}
	return filepath.Clean(filepath.Join("knowledge", "language-modes.json"))
}

func ids(reg Registry) []string {
	out := make([]string, 0, len(reg.Modes))
	for id := range reg.Modes {
		out = append(out, id)
	}
	sort.Strings(out)
	return out
}

func run(args []string, reg Registry) (string, int) {
	if len(args) == 0 || args[0] == "help" || args[0] == "--help" || args[0] == "-h" {
		return "usage: pcx-modes list | show <language> | normalize <alias>\n", 0
	}
	switch args[0] {
	case "list":
		return strings.Join(ids(reg), "\n") + "\n", 0
	case "normalize":
		if len(args) != 2 {
			return "usage: pcx-modes normalize <alias>\n", 2
		}
		id, ok := normalize(reg, args[1])
		if !ok {
			return fmt.Sprintf("unsupported language: %s\n", args[1]), 1
		}
		return id + "\n", 0
	case "show":
		if len(args) != 2 {
			return "usage: pcx-modes show <language>\n", 2
		}
		id, ok := normalize(reg, args[1])
		if !ok {
			return fmt.Sprintf("unsupported language: %s\n", args[1]), 1
		}
		body, err := json.MarshalIndent(reg.Modes[id], "", "  ")
		if err != nil {
			return err.Error() + "\n", 1
		}
		return string(body) + "\n", 0
	default:
		return fmt.Sprintf("unknown command: %s\n", args[0]), 2
	}
}

func main() {
	reg, err := loadRegistry(registryPath())
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	out, code := run(os.Args[1:], reg)
	if code == 0 {
		fmt.Print(out)
	} else {
		fmt.Fprint(os.Stderr, out)
	}
	os.Exit(code)
}
