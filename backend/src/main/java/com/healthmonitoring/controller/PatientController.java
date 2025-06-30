package com.healthmonitoring.controller;

import com.healthmonitoring.dto.HealthMetricDto;
import com.healthmonitoring.dto.PatientProfileDto;
import com.healthmonitoring.dto.DeviceDto;
import com.healthmonitoring.service.PatientService;
import com.healthmonitoring.service.HealthMetricService;
import com.healthmonitoring.service.DeviceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * REST controller for patient-related operations
 * Handles patient profile management, health metrics, and device management
 */
@RestController
@RequestMapping("/api/v1/patient")
@Tag(name = "Patient", description = "Patient management and health monitoring endpoints")
public class PatientController {

    @Autowired
    private PatientService patientService;

    @Autowired
    private HealthMetricService healthMetricService;

    @Autowired
    private DeviceService deviceService;

    @GetMapping("/profile")
    @Operation(summary = "Get patient profile", description = "Retrieve the authenticated patient's profile")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<PatientProfileDto> getProfile(@AuthenticationPrincipal Jwt jwt) {
        String patientId = jwt.getSubject();
        PatientProfileDto profile = patientService.getPatientProfile(patientId);
        return ResponseEntity.ok(profile);
    }

    @PutMapping("/profile")
    @Operation(summary = "Update patient profile", description = "Update the authenticated patient's profile")
    @PreAuthorize("hasRole('PATIENT')")
    public ResponseEntity<PatientProfileDto> updateProfile(
            @AuthenticationPrincipal Jwt jwt,
            @Valid @RequestBody PatientProfileDto profileDto) {
        String patientId = jwt.getSubject();
        PatientProfileDto updatedProfile = patientService.updatePatientProfile(patientId, profileDto);
        return ResponseEntity.ok(updatedProfile);
    }

    @GetMapping("/health-metrics")
    @Operation(summary = "Get health metrics", description = "Retrieve patient's health metrics with optional filtering")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<Page<HealthMetricDto>> getHealthMetrics(
            @AuthenticationPrincipal Jwt jwt,
            @Parameter(description = "Metric type filter") @RequestParam(required = false) String metricType,
            @Parameter(description = "Start time filter") @RequestParam(required = false) 
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startTime,
            @Parameter(description = "End time filter") @RequestParam(required = false) 
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endTime,
            Pageable pageable) {
        
        String patientId = jwt.getSubject();
        Page<HealthMetricDto> metrics = healthMetricService.getPatientMetrics(
            patientId, metricType, startTime, endTime, pageable);
        return ResponseEntity.ok(metrics);
    }

    @GetMapping("/health-metrics/latest")
    @Operation(summary = "Get latest health metrics", description = "Retrieve the most recent health metrics for each type")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<List<HealthMetricDto>> getLatestHealthMetrics(@AuthenticationPrincipal Jwt jwt) {
        String patientId = jwt.getSubject();
        List<HealthMetricDto> latestMetrics = healthMetricService.getLatestMetrics(patientId);
        return ResponseEntity.ok(latestMetrics);
    }

    @GetMapping("/health-metrics/summary")
    @Operation(summary = "Get health metrics summary", description = "Get aggregated health metrics summary")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<?> getHealthMetricsSummary(
            @AuthenticationPrincipal Jwt jwt,
            @Parameter(description = "Summary period (day, week, month)") @RequestParam(defaultValue = "week") String period) {
        
        String patientId = jwt.getSubject();
        var summary = healthMetricService.getHealthMetricsSummary(patientId, period);
        return ResponseEntity.ok(summary);
    }

    @GetMapping("/devices")
    @Operation(summary = "Get patient devices", description = "Retrieve all devices associated with the patient")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<List<DeviceDto>> getDevices(@AuthenticationPrincipal Jwt jwt) {
        String patientId = jwt.getSubject();
        List<DeviceDto> devices = deviceService.getPatientDevices(patientId);
        return ResponseEntity.ok(devices);
    }

    @PostMapping("/devices")
    @Operation(summary = "Register device", description = "Register a new device for the patient")
    @PreAuthorize("hasRole('PATIENT')")
    public ResponseEntity<DeviceDto> registerDevice(
            @AuthenticationPrincipal Jwt jwt,
            @Valid @RequestBody DeviceDto deviceDto) {
        
        String patientId = jwt.getSubject();
        DeviceDto registeredDevice = deviceService.registerDevice(patientId, deviceDto);
        return ResponseEntity.ok(registeredDevice);
    }

    @PutMapping("/devices/{deviceId}")
    @Operation(summary = "Update device", description = "Update device configuration")
    @PreAuthorize("hasRole('PATIENT')")
    public ResponseEntity<DeviceDto> updateDevice(
            @AuthenticationPrincipal Jwt jwt,
            @PathVariable String deviceId,
            @Valid @RequestBody DeviceDto deviceDto) {
        
        String patientId = jwt.getSubject();
        DeviceDto updatedDevice = deviceService.updateDevice(patientId, deviceId, deviceDto);
        return ResponseEntity.ok(updatedDevice);
    }

    @DeleteMapping("/devices/{deviceId}")
    @Operation(summary = "Remove device", description = "Remove a device from the patient's account")
    @PreAuthorize("hasRole('PATIENT')")
    public ResponseEntity<Void> removeDevice(
            @AuthenticationPrincipal Jwt jwt,
            @PathVariable String deviceId) {
        
        String patientId = jwt.getSubject();
        deviceService.removeDevice(patientId, deviceId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/alerts")
    @Operation(summary = "Get health alerts", description = "Retrieve patient's health alerts")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<?> getHealthAlerts(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(defaultValue = "false") boolean unreadOnly,
            Pageable pageable) {
        
        String patientId = jwt.getSubject();
        var alerts = patientService.getHealthAlerts(patientId, unreadOnly, pageable);
        return ResponseEntity.ok(alerts);
    }

    @PutMapping("/alerts/{alertId}/read")
    @Operation(summary = "Mark alert as read", description = "Mark a health alert as read")
    @PreAuthorize("hasRole('PATIENT')")
    public ResponseEntity<Void> markAlertAsRead(
            @AuthenticationPrincipal Jwt jwt,
            @PathVariable String alertId) {
        
        String patientId = jwt.getSubject();
        patientService.markAlertAsRead(patientId, alertId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/statistics")
    @Operation(summary = "Get health statistics", description = "Get patient's health statistics and trends")
    @PreAuthorize("hasRole('PATIENT') or hasRole('CLINICIAN') or hasRole('ADMIN')")
    public ResponseEntity<?> getHealthStatistics(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(defaultValue = "month") String period) {
        
        String patientId = jwt.getSubject();
        var statistics = patientService.getHealthStatistics(patientId, period);
        return ResponseEntity.ok(statistics);
    }
}