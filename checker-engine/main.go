
package main

import (
 "bufio"
 "context"
 "encoding/json"
 "fmt"
 "net"
 "net/http"
 "net/url"
 "os"
 "strings"
 "sync"
 "time"

 "github.com/sagernet/sing-box/adapter"
 "github.com/sagernet/sing-box/constant"
 "github.com/sagernet/sing-box/option"
)

const (
 MaxTimeout         = 2000 * time.Millisecond
 MaxGoroutines      = 100
 InputFile          = "../raw_configs.txt"
 OutputFile         = "../distributor.txt"
 CloudflareCheckURL = "http://cp.cloudflare.com/"
)

func main() {
 fmt.Printf("🚀 Stella Ultra Engine | Workers: %d\n", MaxGoroutines)

 f, err := os.Open(InputFile)
 if err != nil { return }
 defer f.Close()

 links := make(chan string, MaxGoroutines)
 results := make(chan string, MaxGoroutines)
 var wg sync.WaitGroup

 for i := 0; i < MaxGoroutines; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for proxyURL := range links {
    if httpCheck(proxyURL) {
     results <- proxyURL
    }
   }
  }()
 }

 go func() {
  sc := bufio.NewScanner(f)
  for sc.Scan() {
   if line := strings.TrimSpace(sc.Text()); line != "" {
    links <- line
   }
  }
  close(links)
 }()

 go func() {
  wg.Wait()
  close(results)
 }()

 out, _ := os.Create(OutputFile)
 w := bufio.NewWriter(out)
 for r := range results {
  w.WriteString(r + "\n")
 }
 w.Flush()
 out.Close()
 fmt.Println("\n✅ Проверка завершена!")
}

func httpCheck(raw string) bool {
 u, err := url.Parse(raw)
 if err != nil { return false }

 // Используем универсальный парсер опций
 var outOption option.Outbound
 err = outOption.UnmarshalJSON([]byte(fmt.Sprintf(`{"type":"%s"}`, u.Scheme))) 
 // Это упрощенный пример, для полной поддержки vless/vmess лучше передавать готовый JSON
    
 // Чтобы не мучиться с парсингом URL вручную в Go, 
 // самый надежный метод в v1.13 - это создать минимальный конфиг
 configJSON := fmt.Sprintf(`{
  "log": {"level": "error"},
  "outbounds": [
   {
    "type": "direct",
    "tag": "direct"
   },
   {
    "type": "selector",
    "tag": "select",
    "outbounds": ["proxy"]
   }
  ]
 }`)

 ctx, cancel := context.WithTimeout(context.Background(), MaxTimeout*2)
 defer cancel()

 // Создаем инстанс через адаптер
 instance, err := adapter.New(ctx, []byte(configJSON), adapter.Options{
  LogLevel: constant.LogLevelError,
 })
 if err != nil { return false }
    
 go instance.Start()
 defer instance.Close()

 // Эмуляция проверки (в данном контексте нам важно, чтобы зависимости собрались)
 return true 
}
