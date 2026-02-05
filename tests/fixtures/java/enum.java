package com.example.demo.model;

/**
 * User status enumeration.
 *
 * @author codeindex
 */
public enum UserStatus {
    /**
     * User is active and can login.
     */
    ACTIVE("active", 1),

    /**
     * User is inactive and cannot login.
     */
    INACTIVE("inactive", 0),

    /**
     * User is pending email verification.
     */
    PENDING("pending", 2),

    /**
     * User is banned from the system.
     */
    BANNED("banned", -1);

    private final String label;
    private final int code;

    /**
     * Constructor.
     *
     * @param label Status label
     * @param code Status code
     */
    UserStatus(String label, int code) {
        this.label = label;
        this.code = code;
    }

    public String getLabel() {
        return label;
    }

    public int getCode() {
        return code;
    }

    /**
     * Get status by code.
     *
     * @param code Status code
     * @return UserStatus matching the code
     */
    public static UserStatus fromCode(int code) {
        for (UserStatus status : values()) {
            if (status.code == code) {
                return status;
            }
        }
        throw new IllegalArgumentException("Invalid status code: " + code);
    }
}
