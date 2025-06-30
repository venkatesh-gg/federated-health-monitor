package com.healthmonitoring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Main application class for the Health Monitoring Backend
 * 
 * This Spring Boot application provides REST APIs and WebSocket endpoints
 * for the federated health monitoring system.
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class HealthMonitoringApplication {

    public static void main(String[] args) {
        SpringApplication.run(HealthMonitoringApplication.class, args);
    }
}