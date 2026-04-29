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
	fmt.Println("🚀 Stella TCP Ultra-Checker v2.5 | High-Speed Mode")

	const (
		inFile  = "raw_configs.txt"      // Исходный файл
		outFile = "alive_tcp_full.txt"   // Результат
		workers = 300                   // Потоки
		timeout = 2 * time.Second       // Таймаут
	)

	// Открываем исходник
	f, err := os.Open(inFile)
	if err != nil {
		fmt.Printf("❌ Ошибка: Файл %s не найден!\n", inFile)
		return
	}
	defer f.Close()

	// Файл для записи
	out, _ := os.Create(outFile)
	defer out.Close()

	tasks := make(chan string, 1000)
	results := make(chan string, 1000)
	var wg sync.WaitGroup

	// Воркеры
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

	// Запись результатов
	doneWriting := make(chan bool)
	go func() {
		writer := bufio.NewWriter(out)
		count := 0
		for res := range results {
			writer.WriteString(res + "\n")
			count++
			if count%100 == 0 {
				fmt.Printf("\r✅ Найдено живых: %d", count)
				writer.Flush()
			}
		}
		writer.Flush()
		doneWriting <- true
	}()

	// Чтение и парсинг
	scanner := bufio.NewScanner(f)
	total := 0
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if !strings.Contains(line, "://") {
			continue
		}

		u, err := url.Parse(line)
		if err != nil {
			continue
		}

		host := u.Hostname()
		port := u.Port()
		if port == "" {
			port = "443"
		}

		if host != "" {
			tasks <- net.JoinHostPort(host, port)
			total++
		}
	}

	close(tasks)
	wg.Wait()
	close(results)
	<-doneWriting

	fmt.Printf("\n\n🏁 ГОТОВО! Обработано: %d | Результаты в: %s\n", total, outFile)
}
