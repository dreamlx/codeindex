package com.example.demo.controller;

import com.example.demo.model.User;
import com.example.demo.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * User REST API controller.
 * Provides endpoints for user management.
 *
 * @author codeindex
 */
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    /**
     * Get all users.
     *
     * @return List of all users
     */
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        List<User> users = userService.findAll();
        return ResponseEntity.ok(users);
    }

    /**
     * Get user by ID.
     *
     * @param id User ID
     * @return User if found
     */
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Create new user.
     *
     * @param user User to create
     * @return Created user
     */
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User created = userService.save(user);
        return ResponseEntity.ok(created);
    }

    /**
     * Update existing user.
     *
     * @param id User ID
     * @param user Updated user data
     * @return Updated user
     */
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(
        @PathVariable Long id,
        @RequestBody User user
    ) {
        user.setId(id);
        User updated = userService.save(user);
        return ResponseEntity.ok(updated);
    }

    /**
     * Delete user by ID.
     *
     * @param id User ID
     * @return No content if successful
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        boolean deleted = userService.deleteById(id);
        return deleted
            ? ResponseEntity.noContent().build()
            : ResponseEntity.notFound().build();
    }

    /**
     * Search users by name.
     *
     * @param name Name to search
     * @return List of matching users
     */
    @GetMapping("/search")
    public ResponseEntity<List<User>> searchUsers(@RequestParam String name) {
        List<User> users = userService.searchByName(name);
        return ResponseEntity.ok(users);
    }
}
