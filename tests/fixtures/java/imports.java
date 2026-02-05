package com.example.demo;

// Standard library imports
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.Optional;
import java.util.stream.Collectors;

// Static imports
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

// Wildcard import
import java.io.*;

// Third-party imports
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * Test class for import extraction.
 */
@Service
public class ImportTest {

    @Autowired
    private UserService userService;

    public List<String> getNames() {
        return emptyList();
    }

    public Map<String, Object> getData() {
        return new HashMap<>();
    }
}
