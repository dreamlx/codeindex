package com.example.demo.util;

import java.util.List;
import java.util.Map;

/**
 * Generic container class.
 *
 * @param <T> The type of element stored in this box
 */
public class Box<T> {
    private T value;

    public Box(T value) {
        this.value = value;
    }

    public T getValue() {
        return value;
    }

    public void setValue(T value) {
        this.value = value;
    }

    /**
     * Create a box from a value.
     *
     * @param value The value to box
     * @param <U> The type of the value
     * @return A new Box containing the value
     */
    public static <U> Box<U> of(U value) {
        return new Box<>(value);
    }
}

/**
 * Pair container for two values.
 *
 * @param <K> Type of first value
 * @param <V> Type of second value
 */
class Pair<K, V> {
    private K first;
    private V second;

    public Pair(K first, V second) {
        this.first = first;
        this.second = second;
    }

    public K getFirst() {
        return first;
    }

    public V getSecond() {
        return second;
    }
}

/**
 * Repository with generic CRUD operations.
 *
 * @param <T> Entity type
 * @param <ID> ID type
 */
interface Repository<T, ID> {
    T findById(ID id);
    List<T> findAll();
    T save(T entity);
    void deleteById(ID id);
}
