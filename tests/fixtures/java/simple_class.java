package com.example.demo;

import java.util.List;
import java.util.Optional;

/**
 * User entity class.
 * Represents a user in the system.
 *
 * @author codeindex
 * @since 1.0.0
 */
public class User {
    private Long id;
    private String name;
    private String email;
    private int age;

    /**
     * Default constructor.
     */
    public User() {
    }

    /**
     * Constructor with parameters.
     *
     * @param id User ID
     * @param name User name
     * @param email User email
     */
    public User(Long id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }

    /**
     * Get user by ID.
     *
     * @param id User ID
     * @return User object if found
     * @throws UserNotFoundException if user not found
     */
    public Optional<User> findById(Long id) throws UserNotFoundException {
        if (id == null) {
            throw new IllegalArgumentException("ID cannot be null");
        }
        // Implementation
        return Optional.empty();
    }

    /**
     * Save user to database.
     *
     * @param user User to save
     * @return Saved user with generated ID
     */
    public User save(User user) {
        // Implementation
        return user;
    }

    /**
     * Get all users.
     *
     * @return List of all users
     */
    public List<User> findAll() {
        // Implementation
        return List.of();
    }

    // Getters and setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }
}

class UserNotFoundException extends Exception {
    public UserNotFoundException(String message) {
        super(message);
    }
}
