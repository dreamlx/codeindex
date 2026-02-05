package com.example.demo.repository;

import com.example.demo.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository interface for User entity.
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    /**
     * Find user by email address.
     */
    Optional<User> findByEmail(String email);

    /**
     * Check if user exists by email.
     */
    boolean existsByEmail(String email);

    /**
     * Find users by active status.
     */
    @Query("SELECT u FROM User u WHERE u.active = ?1")
    List<User> findByActive(boolean active);
}
