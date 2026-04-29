
package main

import (
 "bufio"
 "context"
 "fmt"
 "net/http"
 "net/url"
 "os"
 "os/exec"
 "strings"
 "sync"
 "time"
)

const (
 MaxWorkers = 15
 InputFile  = "../raw_configs.txt"
 OutputFile = "../distributor.txt"
 CheckURL   = "http://cp.cloudflare.com/"
)

func main() {
 fmt.Println("🚀 Stella Universal Engine v2.0 | Любые протоколы")
    
 in, err := os.Open(InputFile)
 if err != nil {
  fmt.Printf("❌ Файл %s не найден! Создай его на уровень выше.\n", InputFile)
  return
 }
 defer in.Close()

 links := make(chan string, MaxWorkers)
 results := make(chan string, MaxWorkers)
 var wg sync.WaitGroup

 for i := 0; i < MaxWorkers; i++ {
  wg.Add(1)
  go func(id int) {
   defer wg.Done()
   for link := range links {
    port := 20000 + id
    if checkProxy(link, port) {
     fmt.Printf("✅ [Worker %d] ЖИВОЙ: %s\n", id, link[:30]+"...")
     results <- link
    }
   }
  }(i)
 }

 go func() {
  sc := bufio.NewScanner(in)
  for sc.Scan() {
   if l := strings.TrimSpace(sc.Text()); l != "" { links <- l }
  }
  close(links)
 }()

 go func() { wg.Wait(); close(results) }()

 out, _ := os.Create(OutputFile)
 count := 0
 for r := range results {
  fmt.Fprintln(out, r)
  count++
 }
 out.Close()
 fmt.Printf("\n💎 Готово! Найдено рабочих: %d. Результаты в distributor.txt\n", count)
}

func checkProxy(link string, port int) bool {
 configName := fmt.Sprintf("config_%d.json", port)
    
 // Используем официальное ядро для парсинга ссылки в JSON
 formatCmd := exec.Command("stella-box", "format", "-l", link)
 outboundJSON, err := formatCmd.Output()
 if err != nil { return false }

 fullConfig := fmt.Sprintf(`{"inbounds": [{"type": "mixed", "listen": "127.0.0.1", "listen_port": %d}], "outbounds": [%s]}`, port, string(outboundJSON))
 os.WriteFile(configName, []byte(fullConfig), 0644)
 defer os.Remove(configName)

 ctx, cancel := context.WithCancel(context.Background())
 cmd := exec.CommandContext(ctx, "stella-box", "run", "-c", configName)
 if err := cmd.Start(); err != nil { cancel(); return false }
    
 defer func() { cancel(); cmd.Wait() }()

 time.Sleep(1200 * time.Millisecond) // Время на запуск прокси

 pURL, _ := url.Parse(fmt.Sprintf("http://127.0.0.1:%d", port))
 client := &http.Client{
  Transport: &http.Transport{Proxy: http.ProxyURL(pURL)},
  Timeout:   5 * time.Second,
 }
    
 resp, err := client.Get(CheckURL)
 return err == nil && resp.StatusCode == 200
}
