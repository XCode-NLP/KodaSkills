# Цепочка источников учётных данных: полная реализация

Полная компилируемая цепочка учётных данных для вымышленного провайдера `examplecloud`.
Всё живёт в одном пакете `internal/credentials/`, поэтому его можно покрыть модульными
тестами без всякой машинерии Terraform. Подгони имена, форматы файлов и
набор источников под экосистему своего API — переносится именно структура.

## Содержание

- [Структура пакета](#структура-пакета)
- [Основные типы: Credentials, Provider, ошибки](#основные-типы) — `provider.go`
- [Цепочка](#цепочка) — `chain.go`
- [Статический провайдер](#статический-провайдер) — `static.go`
- [Провайдер окружения](#провайдер-окружения) — `env.go`
- [Файловый провайдер с профилями](#файловый-провайдер-с-профилями) — `file.go`
- [Конструктор цепочки по умолчанию](#конструктор-цепочки-по-умолчанию) — `resolve.go`
- [Модульные тесты](#модульные-тесты)

## Структура пакета

```
internal/credentials/
├── provider.go   # Provider interface, Credentials, ErrNoCredentials, ChainError
├── chain.go      # Chain: ordered resolution, error aggregation
├── static.go     # source 1: provider block values
├── env.go        # source 2: environment variables
├── file.go       # source 3: shared credentials file profiles
├── resolve.go    # NewDefaultChain: assembles the canonical order
└── *_test.go
```

## Основные типы

`provider.go`:

```go
package credentials

import (
	"context"
	"errors"
	"fmt"
	"strings"
)

// ErrNoCredentials signals that a source had nothing to offer and the chain
// should fall through to the next source. Any other error from Retrieve
// means the source was configured but unusable (malformed file, missing
// profile) and must be surfaced to the user, not silently skipped.
var ErrNoCredentials = errors.New("no credentials found")

// Credentials is a complete set of secrets. Secrets are resolved as a set:
// a source that supplies only one of the two fields supplies nothing.
type Credentials struct {
	APIKey    string
	APISecret string
	Source    string // name of the provider that supplied them
}

func (c Credentials) Complete() bool {
	return c.APIKey != "" && c.APISecret != ""
}

// String and GoString redact the secret so %v, %+v, and %#v can never leak
// it into logs, diagnostics, or wrapped errors.
func (c Credentials) String() string {
	return fmt.Sprintf("Credentials{APIKey: %s, APISecret: ***REDACTED***, Source: %s}", c.APIKey, c.Source)
}

func (c Credentials) GoString() string { return c.String() }

// Provider is one source of credentials. Retrieve returns ErrNoCredentials
// (possibly wrapped) when the source has nothing to offer.
type Provider interface {
	Retrieve(ctx context.Context) (Credentials, error)
	Name() string
}

// ChainError aggregates the outcome of every source the chain consulted, so
// the final diagnostic can show users exactly what was tried and why each
// source was skipped.
type ChainError struct {
	attempts []attempt
}

type attempt struct {
	source string
	err    error
}

func (e *ChainError) record(source string, err error) {
	e.attempts = append(e.attempts, attempt{source: source, err: err})
}

func (e *ChainError) Error() string {
	if len(e.attempts) == 0 {
		return ErrNoCredentials.Error()
	}
	var b strings.Builder
	b.WriteString("no valid credential sources found. Sources tried:")
	for _, a := range e.attempts {
		fmt.Fprintf(&b, "\n  - %s: %s", a.source, a.err)
	}
	return b.String()
}

// Is makes errors.Is(err, ErrNoCredentials) true only when every source
// fell through cleanly. If any source failed hard (e.g. malformed file),
// the caller should show that failure instead of the generic
// "no credentials" guidance.
func (e *ChainError) Is(target error) bool {
	if target != ErrNoCredentials {
		return false
	}
	for _, a := range e.attempts {
		if !errors.Is(a.err, ErrNoCredentials) {
			return false
		}
	}
	return true
}
```

Замечания по дизайну:

- Два поля-секрета показывают поиск набором; API с одним токеном работает
  так же, если `Complete()` проверяет одно поле.
- `Source` существует только ради наблюдаемости — записывай в журнал его, а не секреты.
- `ChainError.Is` — то, что позволяет `Configure` выбрать между сообщением «вот как
  передать учётные данные» и сообщением «твой файл учётных данных сломан»
  одним вызовом `errors.Is`.

## Цепочка

`chain.go`:

```go
package credentials

import "context"

// Chain consults providers in order and returns the first complete set of
// credentials. Every skipped source is recorded so the aggregate error can
// explain the full resolution attempt.
type Chain struct {
	providers []Provider
}

func NewChain(providers ...Provider) *Chain {
	return &Chain{providers: providers}
}

func (c *Chain) Retrieve(ctx context.Context) (Credentials, error) {
	chainErr := &ChainError{}
	for _, p := range c.providers {
		creds, err := p.Retrieve(ctx)
		switch {
		case err != nil:
			// Record and continue: a broken source should not mask a
			// working one later in the chain, but it must appear in the
			// final error if nothing works. (Alternative: fail fast on
			// non-sentinel errors. Continue-and-record is friendlier when
			// e.g. a stale credentials file exists but env vars are set.)
			chainErr.record(p.Name(), err)
		case !creds.Complete():
			chainErr.record(p.Name(), ErrNoCredentials)
		default:
			creds.Source = p.Name()
			return creds, nil
		}
	}
	return Credentials{}, chainErr
}

func (c *Chain) Name() string { return "Chain" }
```

Цепочка сама реализует `Provider`, поэтому цепочки композируются: источник
удостоверения платформы, который сам является цепочкой эндпоинтов метаданных, встаёт
одной записью.

## Статический провайдер

`static.go` — значения из блока `provider`. Наивысший приоритет: явная
конфигурация всегда побеждает.

```go
package credentials

import "context"

type StaticProvider struct {
	APIKey    string
	APISecret string
}

func (p *StaticProvider) Retrieve(_ context.Context) (Credentials, error) {
	creds := Credentials{APIKey: p.APIKey, APISecret: p.APISecret}
	if !creds.Complete() {
		return Credentials{}, ErrNoCredentials
	}
	return creds, nil
}

func (p *StaticProvider) Name() string { return "provider configuration" }
```

## Провайдер окружения

`env.go` — внедряемое поле `GetEnv` делает модульные тесты приоритета
герметичными (никакого загрязнения между тестами через `os.Setenv`).

```go
package credentials

import (
	"context"
	"os"
)

const (
	EnvAPIKey    = "EXAMPLECLOUD_API_KEY"
	EnvAPISecret = "EXAMPLECLOUD_API_SECRET"
	EnvProfile   = "EXAMPLECLOUD_PROFILE"
	EnvCredsFile = "EXAMPLECLOUD_SHARED_CREDENTIALS_FILE"
)

type EnvProvider struct {
	// GetEnv defaults to os.Getenv; inject a map-backed func in tests.
	GetEnv func(string) string
}

func (p *EnvProvider) getenv(key string) string {
	if p.GetEnv != nil {
		return p.GetEnv(key)
	}
	return os.Getenv(key)
}

func (p *EnvProvider) Retrieve(_ context.Context) (Credentials, error) {
	creds := Credentials{
		APIKey:    p.getenv(EnvAPIKey),
		APISecret: p.getenv(EnvAPISecret),
	}
	if !creds.Complete() {
		return Credentials{}, ErrNoCredentials
	}
	return creds, nil
}

func (p *EnvProvider) Name() string {
	return "environment variables (" + EnvAPIKey + ", " + EnvAPISecret + ")"
}
```

Упоминание реальных переменных в `Name()` напрямую окупается в агрегированном
сообщении об ошибке.

## Файловый провайдер с профилями

`file.go`. Формат здесь — минимальный разбор в стиле INI, чтобы избежать
зависимостей; используй YAML или TOML, если твоя экосистема их предпочитает. Семантика
ошибок — та часть, которую надо скопировать точно.

Правило единообразно: *взятое по умолчанию* значение, которое ни к чему не приводит,
даёт переход дальше; *явное* значение, которое ни к чему не приводит, — ошибка
пользователя и даёт ошибку. Это одинаково относится к пути файла и имени профиля.

| Условие | Поведение | Почему |
|---|---|---|
| Файла нет, путь по умолчанию | `ErrNoCredentials` | У большинства пользователей файла нет; молча идём дальше |
| Файла нет, путь задан явно | жёсткая ошибка | Пользователь указал на него; скажи, что его нет |
| Файл нечитаем или испорчен | жёсткая ошибка | Никогда не пропускай молча файл, который написал пользователь |
| Профиля нет, имя задано явно | жёсткая ошибка | Явный профиль, который ни к чему не приводит, — опечатка |
| Профиля нет, имя по умолчанию | `ErrNoCredentials` | Файл только с именованными профилями не должен ломать тех, кто не просил `default` |
| Профиль есть, поля неполны | `ErrNoCredentials` | Профиль может намеренно содержать только несекретные настройки |

```go
package credentials

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

const DefaultProfile = "default"

func DefaultCredentialsFilePath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".examplecloud", "credentials")
}

// ResolveFilePath: explicit config > env var > default location.
func ResolveFilePath(explicit string, getenv func(string) string) (path string, explicitlySet bool) {
	if explicit != "" {
		return explicit, true
	}
	if fromEnv := getenv(EnvCredsFile); fromEnv != "" {
		return fromEnv, true
	}
	return DefaultCredentialsFilePath(), false
}

// ResolveProfile: explicit config > env var > "default". The explicitlySet
// result feeds the same defaulted-vs-explicit semantics as the file path.
func ResolveProfile(explicit string, getenv func(string) string) (profile string, explicitlySet bool) {
	if explicit != "" {
		return explicit, true
	}
	if fromEnv := getenv(EnvProfile); fromEnv != "" {
		return fromEnv, true
	}
	return DefaultProfile, false
}

type FileProvider struct {
	Path            string // resolved via ResolveFilePath
	PathExplicit    bool   // missing file: hard error if true, fall through if not
	Profile         string // resolved via ResolveProfile
	ProfileExplicit bool   // missing profile: hard error if true, fall through if not
}

func (p *FileProvider) Retrieve(_ context.Context) (Credentials, error) {
	if p.Path == "" {
		return Credentials{}, ErrNoCredentials
	}
	profiles, err := parseCredentialsFile(p.Path)
	if errors.Is(err, fs.ErrNotExist) {
		if p.PathExplicit {
			return Credentials{}, fmt.Errorf("credentials file %q does not exist", p.Path)
		}
		return Credentials{}, ErrNoCredentials
	}
	if err != nil {
		return Credentials{}, fmt.Errorf("reading credentials file %q: %w", p.Path, err)
	}
	profile, ok := profiles[p.Profile]
	if !ok {
		if p.ProfileExplicit {
			return Credentials{}, fmt.Errorf("profile %q not found in %q", p.Profile, p.Path)
		}
		return Credentials{}, ErrNoCredentials
	}
	creds := Credentials{APIKey: profile["api_key"], APISecret: profile["api_secret"]}
	if !creds.Complete() {
		return Credentials{}, ErrNoCredentials
	}
	return creds, nil
}

func (p *FileProvider) Name() string {
	return fmt.Sprintf("shared credentials file (%s, profile %q)", p.Path, p.Profile)
}

// PermissionsTooOpen reports whether the file is group- or world-accessible.
// Surface this as a warning diagnostic, not an error. POSIX permission bits
// are not meaningful on Windows.
func PermissionsTooOpen(path string) bool {
	if runtime.GOOS == "windows" {
		return false
	}
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return info.Mode().Perm()&0o077 != 0
}

// parseCredentialsFile reads a minimal INI format:
//
//	[default]
//	api_key = abc
//	api_secret = xyz
func parseCredentialsFile(path string) (map[string]map[string]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	profiles := map[string]map[string]string{}
	var current map[string]string
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		switch {
		case line == "" || strings.HasPrefix(line, "#"):
		case strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]"):
			name := strings.TrimSpace(line[1 : len(line)-1])
			current = map[string]string{}
			profiles[name] = current
		default:
			key, value, found := strings.Cut(line, "=")
			if !found || current == nil {
				return nil, fmt.Errorf("malformed line: %q", line)
			}
			current[strings.TrimSpace(key)] = strings.TrimSpace(value)
		}
	}
	return profiles, scanner.Err()
}
```

## Конструктор цепочки по умолчанию

`resolve.go` — один конструктор владеет каноническим порядком, чтобы `Configure` и
тесты никогда не расходились в приоритете.

```go
package credentials

import "os"

type Options struct {
	FilePath string // explicit credentials_file from provider config
	Profile  string // explicit profile from provider config
	GetEnv   func(string) string

	// DefaultFilePath overrides the default file location when the user set
	// nothing (keeps defaulted fall-through semantics). Tests use this to
	// stay hermetic without hand-assembling the chain.
	DefaultFilePath string
}

// NewDefaultChain assembles the canonical resolution order:
// static provider configuration > environment variables > credentials file.
// Add a platform identity provider at the end where the platform offers one.
func NewDefaultChain(staticKey, staticSecret string, opts Options) *Chain {
	getenv := opts.GetEnv
	if getenv == nil {
		getenv = os.Getenv
	}
	path, pathExplicit := ResolveFilePath(opts.FilePath, getenv)
	if !pathExplicit && opts.DefaultFilePath != "" {
		path = opts.DefaultFilePath
	}
	profile, profileExplicit := ResolveProfile(opts.Profile, getenv)
	return NewChain(
		&StaticProvider{APIKey: staticKey, APISecret: staticSecret},
		&EnvProvider{GetEnv: getenv},
		&FileProvider{Path: path, PathExplicit: pathExplicit, Profile: profile, ProfileExplicit: profileExplicit},
	)
}
```

Про подключение в `Configure` — защиту от неизвестных значений, ветку `errors.Is`,
выбирающую нужную диагностику, и предупреждение о правах — смотри тело навыка
(SKILL.md); оно напрямую сочетается с этим пакетом.

## Модульные тесты

Основное покрытие, герметичное за счёт внедрённого окружения и `t.TempDir()`:

```go
package credentials

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func mapEnv(m map[string]string) func(string) string {
	return func(key string) string { return m[key] }
}

func writeCredentialsFile(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "credentials")
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

const sampleFile = "[default]\napi_key = file-key\napi_secret = file-secret\n"

func TestChain_StaticWins(t *testing.T) {
	env := mapEnv(map[string]string{EnvAPIKey: "env-key", EnvAPISecret: "env-secret"})
	chain := NewDefaultChain("static-key", "static-secret", Options{GetEnv: env})
	creds, err := chain.Retrieve(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if creds.APIKey != "static-key" {
		t.Errorf("expected static credentials to win, got source %q", creds.Source)
	}
}

func TestChain_EnvBeatsFile(t *testing.T) {
	path := writeCredentialsFile(t, sampleFile)
	env := mapEnv(map[string]string{EnvAPIKey: "env-key", EnvAPISecret: "env-secret"})
	chain := NewDefaultChain("", "", Options{FilePath: path, GetEnv: env})
	creds, err := chain.Retrieve(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if creds.APIKey != "env-key" {
		t.Errorf("expected env credentials to win, got %q from %q", creds.APIKey, creds.Source)
	}
}

func TestChain_FallsThroughToFile(t *testing.T) {
	path := writeCredentialsFile(t, sampleFile)
	chain := NewDefaultChain("", "", Options{FilePath: path, GetEnv: mapEnv(nil)})
	creds, err := chain.Retrieve(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if creds.APIKey != "file-key" {
		t.Errorf("expected file credentials, got %q from %q", creds.APIKey, creds.Source)
	}
}

func TestChain_IncompleteSourceSkipped(t *testing.T) {
	// Env supplies only the key: the set is incomplete, so the whole
	// source is skipped and the file supplies both values.
	path := writeCredentialsFile(t, sampleFile)
	env := mapEnv(map[string]string{EnvAPIKey: "env-key"})
	chain := NewDefaultChain("", "", Options{FilePath: path, GetEnv: env})
	creds, err := chain.Retrieve(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if creds.APIKey != "file-key" {
		t.Errorf("incomplete env source must not win: got %q from %q", creds.APIKey, creds.Source)
	}
}

func TestChain_AllSourcesEmpty(t *testing.T) {
	chain := NewDefaultChain("", "", Options{
		DefaultFilePath: filepath.Join(t.TempDir(), "missing"), // defaulted semantics, hermetic location
		GetEnv:          mapEnv(nil),
	})
	_, err := chain.Retrieve(context.Background())
	if !errors.Is(err, ErrNoCredentials) {
		t.Fatalf("expected ErrNoCredentials, got %v", err)
	}
	for _, source := range []string{"provider configuration", "environment variables", "credentials file"} {
		if !strings.Contains(err.Error(), source) {
			t.Errorf("aggregate error should mention %q:\n%s", source, err)
		}
	}
}

func TestChain_ExplicitMissingProfileIsHardError(t *testing.T) {
	path := writeCredentialsFile(t, sampleFile)
	chain := NewDefaultChain("", "", Options{FilePath: path, Profile: "prod", GetEnv: mapEnv(nil)})
	_, err := chain.Retrieve(context.Background())
	if err == nil || errors.Is(err, ErrNoCredentials) {
		t.Fatalf("expected hard error for missing profile, got %v", err)
	}
	if !strings.Contains(err.Error(), `profile "prod" not found`) {
		t.Errorf("error should name the missing profile:\n%s", err)
	}
}

func TestChain_DefaultProfileMissingFallsThrough(t *testing.T) {
	// The file exists but holds only a named profile; nobody asked for
	// "default", so the file source falls through instead of erroring.
	path := writeCredentialsFile(t, "[work]\napi_key = k\napi_secret = s\n")
	chain := NewDefaultChain("", "", Options{FilePath: path, GetEnv: mapEnv(nil)})
	_, err := chain.Retrieve(context.Background())
	if !errors.Is(err, ErrNoCredentials) {
		t.Fatalf("expected fall-through for defaulted missing profile, got %v", err)
	}
}

func TestCredentials_Redaction(t *testing.T) {
	creds := Credentials{APIKey: "key", APISecret: "super-secret"}
	for _, formatted := range []string{
		fmt.Sprintf("%v", creds), fmt.Sprintf("%+v", creds), fmt.Sprintf("%#v", creds), creds.String(),
	} {
		if strings.Contains(formatted, "super-secret") {
			t.Errorf("secret leaked: %s", formatted)
		}
	}
}
```
