package com.example.demo.service;

import com.example.demo.User;
import java.util.List;
import java.util.Optional;

/**
 * User service interface.
 * Defines operations for user management.
 *
 * @author codeindex
 */
public interface UserService {

    /**
     * Find user by ID.
     *
     * @param id User ID
     * @return Optional containing user if found
     */
    Optional<User> findById(Long id);

    /**
     * Find all users.
     *
     * @return List of all users
     */
    List<User> findAll();

    /**
     * Save user.
     *
     * @param user User to save
     * @return Saved user
     */
    User save(User user);

    /**
     * Delete user by ID.
     *
     * @param id User ID
     * @return true if deleted, false otherwise
     */
    boolean deleteById(Long id);

    /**
     * Count total users.
     *
     * @return Total number of users
     */
    long count();
}
