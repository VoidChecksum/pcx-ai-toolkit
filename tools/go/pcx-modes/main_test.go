package main

import "testing"

func testRegistry() Registry {
	return Registry{
		Default: "enma",
		Modes: map[string]Mode{
			"enma": {
				ID:         "enma",
				Aliases:    []string{"enma", "em", ".em"},
				Extensions: []string{".em"},
			},
			"angelscript": {
				ID:         "angelscript",
				Aliases:    []string{"angelscript", "angel-script", "as", ".as"},
				Extensions: []string{".as"},
			},
		},
	}
}

func TestNormalizeAliases(t *testing.T) {
	reg := testRegistry()
	cases := map[string]string{
		"":             "enma",
		".em":          "enma",
		"angel-script": "angelscript",
		"as":           "angelscript",
		".as":          "angelscript",
	}
	for input, want := range cases {
		got, ok := normalize(reg, input)
		if !ok || got != want {
			t.Fatalf("normalize(%q) = %q, %v; want %q, true", input, got, ok, want)
		}
	}
}

func TestRunListAndShow(t *testing.T) {
	reg := testRegistry()
	out, code := run([]string{"list"}, reg)
	if code != 0 || out != "angelscript\nenma\n" {
		t.Fatalf("list = code %d output %q", code, out)
	}
	out, code = run([]string{"show", "as"}, reg)
	if code != 0 || out == "" {
		t.Fatalf("show as = code %d output %q", code, out)
	}
}
