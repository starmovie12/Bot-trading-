// Package main: Pehredaar (watchdog). M0 mein sirf Lease ka niyam; broker se koi connection nahi.
//
// Niyam (idea v4, F-05): Bot ka Lease hamesha Pehredaar ke control lene ke samay se chhota ho,
// taaki Pehredaar ke control lene se pehle Bot khud broker ko hukm bhejna band kar de.
package main

import (
	"errors"
	"time"
)

// Lease: Bot ka broker ko hukm bhejne ka chhota haq. Har Pehredaar pushti (ack) par naya hota hai.
type Lease struct {
	LastAck  time.Time
	Duration time.Duration
}

// Valid batata hai ki is pal Bot ka Lease chalu hai ya nahi.
func (l Lease) Valid(now time.Time) bool {
	if l.LastAck.IsZero() || l.Duration <= 0 {
		return false
	}
	return now.Sub(l.LastAck) < l.Duration
}

// TakeoverAfter: Pehredaar itni der dhadkan na mile toh control leta hai (dhadkan ka samay x chhoot ginti).
func TakeoverAfter(heartbeat time.Duration, misses int) time.Duration {
	return heartbeat * time.Duration(misses)
}

// ErrUnsafeLease: Lease takeover samay se chhota nahi hai; dono ek saath broker ko hukm de sakte hain.
var ErrUnsafeLease = errors.New("Bot_Lease_Samay Pehredaar ke control samay se chhota hona chahiye (F-05)")

// CheckLeaseSafe config ke numbers ka niyam jaanchta hai.
func CheckLeaseSafe(lease, heartbeat time.Duration, misses int) error {
	if lease <= 0 || heartbeat <= 0 || misses <= 0 {
		return errors.New("lease, heartbeat aur misses positive hone chahiye")
	}
	if lease >= TakeoverAfter(heartbeat, misses) {
		return ErrUnsafeLease
	}
	return nil
}
