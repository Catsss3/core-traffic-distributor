
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

 "github.com/SagerNet/sing-box/common/json"
 "github.com/SagerNet/sing-box/constant"
 "github.com/SagerNet/sing-box/driver"
 "github.com/SagerNet/sing-box/outbound"
 "github.com/SagerNet/sing-box/proxy"
)

const (
 TCPTimeout         = 1200 * time.Millisecond
 HTTPTimeout        = 2500 * time.Millisecond
 MaxGoroutines      = 150
 InputFile          = "../raw_configs.txt" # Поднимаемся на уровень выше к конфигам
 OutputFile         = "../distributor.txt" # Пишем результат тоже в корень
 CloudflareCheckURL = "http://cp.cloudflare.com/"
)

func main() {
 fmt.Printf("🚀 Stella Turbo-Engine | Workers: %d\n", MaxGoroutines)

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
   line := strings.TrimSpace(sc.Text())
   if line != "" {
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
 defer out.Close()
 w := bufio.NewWriter(out)

 cnt := 0
 for r := range results {
  w.WriteString(r + "\n")
  cnt++
  if cnt%100 == 0 {
   fmt.Printf("\r🔍 Проверено... Найдено живых: %d", cnt)
  }
 }
 w.Flush()
 fmt.Printf("\n✅ Готово! Результат в distributor.txt\n")
}

func httpCheckSingBox(raw string) bool {
 u, err := url.Parse(raw)
 if err != nil || u.Host == "" { return false }
 if !tcpAlive(u.Host) { return false }

 ob, err := proxy.ParseURL(u)
 if err != nil { return false }

 opt, err := outbound.NewOption(ob)
 if err != nil { return false }
 outJSON, _ := json.Marshal(opt)

 conf := map[string]any{
  "log": map[string]any{"level": "error"},
  "outbounds": []json.RawMessage{outJSON},
 }
 confBytes, _ := json.Marshal(conf)

 ctx, cancel := context.WithTimeout(context.Background(), HTTPTimeout*2)
 defer cancel()

 d, err := driver.New(ctx, confBytes, driver.Options{LogLevel: constant.LogLevelError})
 if err != nil { return false }
 go d.Start()
 defer d.Close()

 time.Sleep(120 * time.Millisecond)

 client := &http.Client{
  Transport: &http.Transport{
   DialContext: func(c context.Context, n, a string) (net.Conn, error) {
    return d.DialContext(c, n, a)
   },
  },
  Timeout: HTTPTimeout,
 }

 req, _ := http.NewRequestWithContext(ctx, "GET", CloudflareCheckURL, nil)
 resp, err := client.Do(req)
 if err != nil { return false }
 defer resp.Body.Close()

 return resp.StatusCode == http.StatusOK
}

func tcpAlive(hostPort string) bool {
 if !strings.Contains(hostPort, ":") { hostPort += ":443" }
 conn, err := net.DialTimeout("tcp", hostPort, TCPTimeout)
 if err != nil { return false }
 conn.Close()
 return true
}
