package main

import (
	"errors"
	"testing"
	"time"
)

func TestLeaseValid(t *testing.T) {
	t0 := time.Date(2026, 11, 10, 9, 15, 0, 0, time.UTC)
	l := Lease{LastAck: t0, Duration: 4 * time.Second}
	cases := []struct {
		after time.Duration
		want  bool
	}{
		{0, true},
		{3999 * time.Millisecond, true},
		{4 * time.Second, false}, // theek seema par Lease khatam
		{10 * time.Second, false},
	}
	for _, c := range cases {
		if got := l.Valid(t0.Add(c.after)); got != c.want {
			t.Errorf("after %v: got %v want %v", c.after, got, c.want)
		}
	}
	if (Lease{}).Valid(t0) {
		t.Error("khaali Lease kabhi valid nahi")
	}
}

func TestCheckLeaseSafe(t *testing.T) {
	if err := CheckLeaseSafe(4*time.Second, 2*time.Second, 3); err != nil {
		t.Fatalf("idea ke numbers (4s < 6s) safe hone chahiye: %v", err)
	}
	if err := CheckLeaseSafe(6*time.Second, 2*time.Second, 3); !errors.Is(err, ErrUnsafeLease) {
		t.Fatalf("6s >= 6s unsafe hona chahiye, mila: %v", err)
	}
	if err := CheckLeaseSafe(0, 2*time.Second, 3); err == nil {
		t.Fatal("zero lease par error chahiye")
	}
}
