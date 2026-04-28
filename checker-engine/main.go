
package main

import (
 "bufio"
 "context"
 "fmt"
 "net"
 "net/http"
 "net/url"
 "os"
 "strings"
 "sync"
 "time"
    "encoding/json" // Стандартный JSON для RawMessage

 "github.com/sagernet/sing-box/adapter"
 "github.com/sagernet/sing-box/common"
 "github.com/sagernet/sing-box/constant"
 "github.com/sagernet/sing-box/outbound"
 "github.com/sagernet/sing-box/proxy"
)

const (
 MaxTimeout         = 1800 * time.Millisecond
 MaxGoroutines      = 150
 InputFile          = "../raw_configs.txt"
 OutputFile         = "../distributor.txt"
 CloudflareCheckURL = "http://cp.cloudflare.com/"
)

func main() {
 fmt.Printf("🛡️ Stella + Sing-Box Engine (v1.13+) | Workers %d\n", MaxGoroutines)

 f, err := os.Open(InputFile)
 if err != nil {
  fmt.Printf("❌ Ошибка: %s не найден\n", InputFile)
  return
 }
 defer f.Close()

 links := make(chan string, MaxGoroutines)
 results := make(chan string, MaxGoroutines)
 var wg sync.WaitGroup

 for i := 0; i < MaxGoroutines; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for proxyURL := range links {
    if httpCheckSingBox(proxyURL) {
     results <- proxyURL
    }
   }
  }()
 }

 go func() {
  sc := bufio.NewScanner(f)
  for sc.Scan() {
   links <- sc.Text()
  }
  close(links)
 }()

 go func() {
  wg.Wait()
  close(results)
 }()

 out, _ := os.Create(OutputFile)
 defer out.Close()
 w := bufio.NewWriter(out)

 cnt := 0
 for r := range results {
  w.WriteString(r + "\n")
  cnt++
  if cnt%100 == 0 {
   fmt.Printf("\r🔍 Проверено... Живых: %d", cnt)
  }
 }
 w.Flush()
 fmt.Printf("\n🏁 Готово! Результат записан в %s\n", OutputFile)
}

func httpCheckSingBox(raw string) bool {
 raw = strings.TrimSpace(raw)
 if raw == "" || !strings.Contains(raw, "://") { return false }

 ob, err := parseProxyURL(raw)
 if err != nil { return false }

 opt, err := outbound.NewOption(ob)
 if err != nil { return false }
    
 outJSON, err := common.Marshal(opt)
 if err != nil { return false }

 conf := map[string]any{
  "log": map[string]any{"level": "error"},
  "outbounds": []json.RawMessage{outJSON},
 }
 confBytes, _ := common.Marshal(conf)

 ctx, cancel := context.WithTimeout(context.Background(), MaxTimeout*2)
 defer cancel()

 d, err := adapter.New(ctx, confBytes, adapter.Options{
  LogLevel: constant.LogLevelError,
 })
 if err != nil { return false }
 go func() { _ = d.Start() }()

 time.Sleep(150 * time.Millisecond)

 client := &http.Client{
  Transport: &http.Transport{
   DialContext: func(c context.Context, n, a string) (net.Conn, error) {
    return d.DialContext(c, n, a)
   },
  },
  Timeout: MaxTimeout,
 }

 req, _ := http.NewRequestWithContext(ctx, "GET", CloudflareCheckURL, nil)
 resp, err := client.Do(req)
 if err != nil {
  _ = d.Close()
  return false
 }
 defer resp.Body.Close()
 _ = d.Close()

 return resp.StatusCode == http.StatusOK
}

func parseProxyURL(raw string) (proxy.Outbound, error) {
 u, err := url.Parse(raw)
 if err != nil { return nil, err }
 return proxy.ParseURL(u)
}
