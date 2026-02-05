package com.example.demo.model;

/**
 * Sealed shape class (Java 17+ feature).
 * Only permits Circle, Rectangle, and Triangle subclasses.
 */
public sealed class Shape permits Circle, Rectangle, Triangle {
    protected final String color;

    public Shape(String color) {
        this.color = color;
    }

    public String getColor() {
        return color;
    }

    /**
     * Calculate area of the shape.
     *
     * @return Area in square units
     */
    public abstract double area();
}

/**
 * Circle shape.
 */
final class Circle extends Shape {
    private final double radius;

    public Circle(String color, double radius) {
        super(color);
        this.radius = radius;
    }

    @Override
    public double area() {
        return Math.PI * radius * radius;
    }

    public double getRadius() {
        return radius;
    }
}

/**
 * Rectangle shape.
 */
final class Rectangle extends Shape {
    private final double width;
    private final double height;

    public Rectangle(String color, double width, double height) {
        super(color);
        this.width = width;
        this.height = height;
    }

    @Override
    public double area() {
        return width * height;
    }
}

/**
 * Triangle shape.
 */
non-sealed class Triangle extends Shape {
    private final double base;
    private final double height;

    public Triangle(String color, double base, double height) {
        super(color);
        this.base = base;
        this.height = height;
    }

    @Override
    public double area() {
        return 0.5 * base * height;
    }
}
