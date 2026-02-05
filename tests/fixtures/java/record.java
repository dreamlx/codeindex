package com.example.demo.model;

import java.time.LocalDate;

/**
 * User record (Java 14+ feature).
 * Immutable data class with automatic getters, equals, hashCode, and toString.
 *
 * @param id User ID
 * @param name User name
 * @param email User email
 * @param createdAt Creation date
 */
public record UserRecord(
    Long id,
    String name,
    String email,
    LocalDate createdAt
) {
    /**
     * Compact constructor for validation.
     */
    public UserRecord {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name cannot be blank");
        }
        if (email == null || !email.contains("@")) {
            throw new IllegalArgumentException("Invalid email");
        }
    }

    /**
     * Create a new user record with updated name.
     *
     * @param newName The new name
     * @return A new UserRecord with updated name
     */
    public UserRecord withName(String newName) {
        return new UserRecord(id, newName, email, createdAt);
    }

    /**
     * Check if user is recently created.
     *
     * @return true if created within last 30 days
     */
    public boolean isRecent() {
        return createdAt.isAfter(LocalDate.now().minusDays(30));
    }
}
