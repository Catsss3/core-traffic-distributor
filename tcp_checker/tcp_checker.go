
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
 fmt.Println("📊 --- Stella Audit System v3.2 ---")
 const (
  inFile  = "raw_configs.txt"
  outFile = "tcp_checker/alive_tcp_full.txt"
  workers = 500 
  timeout = 3 * time.Second
 )

 f, err := os.Open(inFile)
 if err != nil {
  fmt.Println("❌ Ошибка: Файл raw_configs.txt не найден!")
  return
 }
 defer f.Close()

 addrToLinks := make(map[string][]string)
 var totalLines int

 scanner := bufio.NewScanner(f)
 for scanner.Scan() {
  totalLines++
  line := strings.TrimSpace(scanner.Text())
  if line == "" || !strings.Contains(line, "://") {
   continue
  }

  u, err := url.Parse(line)
  if err != nil {
   continue
  }

  host, port := u.Hostname(), u.Port()
  if port == "" {
   switch u.Scheme {
   case "vless", "trojan", "ss": port = "443"
   default: port = "80"
   }
  }
  
  address := net.JoinHostPort(host, port)
  addrToLinks[address] = append(addrToLinks[address], line)
 }

 uniqueAddrs := len(addrToLinks)
 fmt.Printf("📥 ВХОД: Всего строк в файле: %d\n", totalLines)
 fmt.Printf("🎯 ГРУППИРОВКА: Найдено уникальных IP:Port: %d\n", uniqueAddrs)

 tasks := make(chan string, 1000)
 results := make(chan string, 1000)
 var wg sync.WaitGroup

 for i := 0; i < workers; i++ {
  wg.Add(1)
  go func() {
   defer wg.Done()
   for addr := range tasks {
    conn, err := net.DialTimeout("tcp", addr, timeout)
    if err == nil {
     conn.Close()
     results <- addr
    }
   }
  }()
 }

 var aliveAddrCount int
 var aliveLinks []string
 var mu sync.Mutex
 doneWriting := make(chan bool)

 go func() {
  for addr := range results {
   mu.Lock()
   aliveAddrCount++
   aliveLinks = append(aliveLinks, addrToLinks[addr]...)
   mu.Unlock()
  }
  doneWriting <- true
 }()

 for addr := range addrToLinks {
  tasks <- addr
 }
 close(tasks)

 wg.Wait()
 close(results)
 <-doneWriting

 os.MkdirAll("tcp_checker", os.ModePerm)
 out, _ := os.Create(outFile)
 defer out.Close()
 writer := bufio.NewWriter(out)
 for _, link := range aliveLinks {
  writer.WriteString(link + "\n")
 }
 writer.Flush()

 fmt.Println("\n--- ИТОГИ ПРОВЕРКИ ---")
 fmt.Printf("✅ Живых уникальных серверов: %d\n", aliveAddrCount)
 fmt.Printf("❌ Мертвых уникальных серверов: %d\n", uniqueAddrs - aliveAddrCount)
 fmt.Printf("📦 Всего живых ссылок сохранено: %d\n", len(aliveLinks))
}
