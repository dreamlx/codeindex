package com.example.demo.service;

import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * Service layer for user business logic.
 */
@Service
@Transactional
public class UserService {

    @Autowired
    private UserRepository userRepository;

    /**
     * Find all users.
     */
    public List<User> findAll() {
        return userRepository.findAll();
    }

    /**
     * Find user by ID.
     */
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }

    /**
     * Save user.
     */
    public User save(User user) {
        return userRepository.save(user);
    }

    /**
     * Delete user by ID.
     */
    public void deleteById(Long id) {
        userRepository.deleteById(id);
    }

    /**
     * Find user by email.
     */
    public Optional<User> findByEmail(String email) {
        return userRepository.findByEmail(email);
    }
}
