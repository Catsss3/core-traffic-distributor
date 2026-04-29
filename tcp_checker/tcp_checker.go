
package main
import (
 "bufio"
 "fmt"
 "net"
 "net/url"
 "os"
 "strings"
 "sync"
 "time"
)
func main() {
 fmt.Println("🚀 Stella Ultra-Link-Preserver v3.0 | Full Link Check Mode")
 const (
  inFile  = "raw_configs.txt"
  outFile = "alive_tcp_full.txt"
  workers = 300
  timeout = 2 * time.Second
 )
 f, err := os.Open(inFile)
 if err != nil { return }
 defer f.Close()
 out, _ := os.Create(outFile)
 defer out.Close()
 type task struct {
  fullLine string
  address  string
 }
 tasks := make(chan task, 1000)
 results := make(chan string, 1000)
 var wg sync.WaitGroup
 for i := 0; i < workers; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for t := range tasks {
    conn, err := net.DialTimeout("tcp", t.address, timeout)
    if err == nil {
     conn.Close()
     results <- t.fullLine // СОХРАНЯЕМ ПОЛНУЮ ССЫЛКУ
    }
   }
  }()
 }
 doneWriting := make(chan bool)
 go func() {
  writer := bufio.NewWriter(out)
  for res := range results {
   writer.WriteString(res + "\n")
  }
  writer.Flush()
  doneWriting <- true
 }()
 scanner := bufio.NewScanner(f)
 for scanner.Scan() {
  line := strings.TrimSpace(scanner.Text())
  if line == "" || !strings.Contains(line, "://") { continue }
  u, err := url.Parse(line)
  if err != nil { continue }
  host, port := u.Hostname(), u.Port()
  if port == "" { if u.Scheme == "vless" || u.Scheme == "trojan" { port = "443" } else { port = "80" } }
  tasks <- task{fullLine: line, address: net.JoinHostPort(host, port)}
 }
 close(tasks)
 wg.Wait()
 close(results)
 <-doneWriting
 fmt.Println("🏁 Скрипт отработал корректно!")
}
