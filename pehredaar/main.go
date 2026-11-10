package main

import (
	"fmt"
	"os"
	"time"
)

// M0: sirf dhaancha. Asli kaam (broker milaan, Exit Hissa, Kill Latch) M6 mein.
func main() {
	// Idea v4 ke Prastaavit numbers: Bot_Lease_Samay 4s, Pehredaar_Dhadkan_Samay 2s, chhoot ginti 3.
	// M6 mein yeh config/niyam.toml se padhe jaayenge.
	if err := CheckLeaseSafe(4*time.Second, 2*time.Second, 3); err != nil {
		fmt.Fprintln(os.Stderr, "FAIL:", err)
		os.Exit(1)
	}
	fmt.Println("Pehredaar M0: dhaancha theek. Broker se koi connection nahi.")
}
