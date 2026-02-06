<?php
/**
 * Sample PHP module for LoomGraph integration testing.
 *
 * This module demonstrates all features that codeindex extracts for LoomGraph:
 * - Symbols (classes, methods, functions)
 * - Imports (use statements with aliases)
 * - Inheritances (extends, implements)
 */

namespace App\Example;

use DateTime;
use Illuminate\Database\Eloquent\Model as BaseModel;
use Illuminate\Contracts\Auth\Authenticatable;
use App\Traits\Loggable;
use App\Services\{Logger as LogService, Cache};

/**
 * Base repository with common CRUD operations.
 */
abstract class BaseRepository
{
    /**
     * Save entity to database.
     *
     * @return bool Success status
     */
    public function save(): bool
    {
        return true;
    }

    /**
     * Delete entity from database.
     *
     * @return void
     */
    public function delete(): void
    {
        // Implementation here
    }
}

/**
 * Interface for authentication capabilities.
 */
interface AuthenticatableInterface
{
    /**
     * Authenticate with credentials.
     *
     * @param string $password User password
     * @return bool Authentication result
     */
    public function authenticate(string $password): bool;

    /**
     * Get user permissions.
     *
     * @return array List of permissions
     */
    public function getPermissions(): array;
}

/**
 * User model with authentication capabilities.
 *
 * Extends BaseRepository and implements AuthenticatableInterface.
 */
class User extends BaseRepository implements AuthenticatableInterface
{
    /**
     * User's unique username.
     *
     * @var string
     */
    private string $username;

    /**
     * User's email address.
     *
     * @var string
     */
    private string $email;

    /**
     * Account creation timestamp.
     *
     * @var DateTime
     */
    private DateTime $createdAt;

    /**
     * Initialize user account.
     *
     * @param string $username User's unique username
     * @param string $email User's email address
     */
    public function __construct(string $username, string $email)
    {
        $this->username = $username;
        $this->email = $email;
        $this->createdAt = new DateTime();
    }

    /**
     * Authenticate user with password.
     *
     * @param string $password User's password
     * @return bool True if authentication successful
     */
    public function authenticate(string $password): bool
    {
        // Authentication logic here
        return true;
    }

    /**
     * Get user permissions.
     *
     * @return array List of permission names
     */
    public function getPermissions(): array
    {
        return ['read', 'write'];
    }

    /**
     * Get user's email.
     *
     * @return string Email address
     */
    public function getEmail(): string
    {
        return $this->email;
    }
}

/**
 * Admin user with elevated privileges.
 *
 * Extends User to inherit authentication capabilities.
 */
class AdminUser extends User
{
    /**
     * Grant permission to another user.
     *
     * @param int $userId Target user ID
     * @param string $permission Permission name to grant
     * @return bool True if permission granted successfully
     */
    public function grantPermission(int $userId, string $permission): bool
    {
        // Grant logic here
        return true;
    }

    /**
     * Revoke permission from user.
     *
     * @param int $userId Target user ID
     * @param string $permission Permission name to revoke
     * @return bool True if permission revoked successfully
     */
    public function revokePermission(int $userId, string $permission): bool
    {
        // Revoke logic here
        return true;
    }

    /**
     * Get all admin permissions.
     *
     * @return array Extended permission list
     */
    public function getPermissions(): array
    {
        return array_merge(parent::getPermissions(), ['admin', 'grant', 'revoke']);
    }
}

/**
 * Controller class implementing multiple interfaces.
 */
class UserController implements AuthenticatableInterface, \JsonSerializable
{
    /**
     * Authenticate user.
     *
     * @param string $password Password
     * @return bool Result
     */
    public function authenticate(string $password): bool
    {
        return false;
    }

    /**
     * Get permissions.
     *
     * @return array Permissions
     */
    public function getPermissions(): array
    {
        return [];
    }

    /**
     * JSON serialization.
     *
     * @return array Serialized data
     */
    public function jsonSerialize(): array
    {
        return [];
    }
}

/**
 * Retrieve user by ID.
 *
 * @param int $userId User ID to lookup
 * @return User|null User object if found, null otherwise
 */
function getUserById(int $userId): ?User
{
    // Lookup logic here
    return null;
}

/**
 * Create new user account.
 *
 * @param string $username Desired username
 * @param string $email User's email
 * @return User Newly created User object
 */
function createUser(string $username, string $email): User
{
    return new User($username, $email);
}

/**
 * Validate email format.
 *
 * @param string $email Email to validate
 * @return bool True if valid
 */
function validateEmail(string $email): bool
{
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}
