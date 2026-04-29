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
 fmt.Println("🚀 Stella TCP ULTRA-SCAN | Full Power Mode (53k+)")

 const inFile = "raw_configs.txt"
 const outFile = "alive_tcp_full.txt"

 f, err := os.Open(inFile)
 if err != nil {
  fmt.Printf("❌ Ошибка: Файл %s не найден\n", inFile)
  return
 }
 defer f.Close()

 out, _ := os.Create(outFile)
 defer out.Close()

 tasks := make(chan string, 1000)
 results := make(chan string, 1000)
 var wg sync.WaitGroup

 // Агрессивный режим: 300 потоков
 for i := 0; i < 300; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for addr := range tasks {
    conn, err := net.DialTimeout("tcp", addr, 2*time.Second)
    if err == nil {
     conn.Close()
     results <- addr
    }
   }
  }()
 }

 // Отдельная горутина для записи, чтобы не тормозить проверку
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
 count := 0
 for scanner.Scan() {
  line := strings.TrimSpace(scanner.Text())
  if !strings.Contains(line, "://") { continue }

  u, _ := url.Parse(line)
  if u == nil { continue }

  host := u.Hostname()
  port := u.Port()
  if port == "" { port = "443" }

  if host != "" {
   tasks <- net.JoinHostPort(host, port)
   count++
  }
 }

 close(tasks)
 wg.Wait()
 close(results)
 <-doneWriting

 fmt.Printf("\n🏁 МЕГА-СКАН ЗАВЕРШЕН. Проверено: %d. Результаты в %s\n", count, outFile)
}
