package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

const packageSpec = "firstcut"
const errorMessage = "Unable to launch firstcut. Install uv or pipx, or ensure python3 can create a venv for firstcut."

func main() {
	args := os.Args[1:]

	if tryExec("uvx", append([]string{packageSpec}, args...)) {
		return
	}

	if tryExec("pipx", append([]string{"run", packageSpec}, args...)) {
		return
	}

	python, err := findPython()
	if err != nil {
		fmt.Fprintln(os.Stderr, errorMessage)
		os.Exit(1)
	}

	home, err := os.UserHomeDir()
	if err != nil {
		fmt.Fprintln(os.Stderr, errorMessage)
		os.Exit(1)
	}

	venvDir := filepath.Join(home, ".cache", "firstcut-wrapper", "venv")
	cliPath, err := ensureVenv(python, venvDir)
	if err != nil {
		fmt.Fprintln(os.Stderr, errorMessage)
		os.Exit(1)
	}

	cmd := exec.Command(cliPath, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fmt.Fprintln(os.Stderr, errorMessage)
		os.Exit(1)
	}
}

func tryExec(name string, args []string) bool {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		if _, ok := err.(*exec.Error); ok {
			return false
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		return false
	}
	os.Exit(0)
	return true
}

func findPython() (string, error) {
	candidates := []string{"python3", "python"}
	for _, candidate := range candidates {
		if _, err := exec.LookPath(candidate); err == nil {
			return candidate, nil
		}
	}
	return "", fmt.Errorf("python not found")
}

func ensureVenv(python string, venvDir string) (string, error) {
	binDir := filepath.Join(venvDir, "bin")
	pipPath := filepath.Join(binDir, "pip")
	cliPath := filepath.Join(binDir, "firstcut")

	if _, err := os.Stat(cliPath); err == nil {
		return cliPath, nil
	}

	if err := os.MkdirAll(venvDir, 0o755); err != nil {
		return "", err
	}

	create := exec.Command(python, "-m", "venv", venvDir)
	create.Stdout = os.Stdout
	create.Stderr = os.Stderr
	create.Stdin = os.Stdin
	if err := create.Run(); err != nil {
		return "", err
	}

	install := exec.Command(pipPath, "install", packageSpec)
	install.Stdout = os.Stdout
	install.Stderr = os.Stderr
	install.Stdin = os.Stdin
	if err := install.Run(); err != nil {
		return "", err
	}

	return cliPath, nil
}
