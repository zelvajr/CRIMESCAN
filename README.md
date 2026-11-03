# CrimeScan
### AI-Enabled Forensic Scene Documentation & Evidence Management System

CrimeScan is an interdisciplinary engineering project combining computer vision, desktop software, mobile applications and embedded systems to improve crime-scene documentation and evidence management.

The system is designed around structured scene documentation, AI-assisted candidate-evidence identification, evidence integrity verification and human-in-the-loop review.

## Problem

Traditional crime-scene documentation involves multiple disconnected processes for image capture, evidence identification, documentation and reporting.

CrimeScan explores an integrated approach that brings these workflows into a unified technical system while maintaining investigator oversight and evidence traceability.

## System Architecture

The platform consists of four major components:

**1. Desktop Application**
- Python and PyQt6 application.
- Live scene viewing and video-frame extraction.
- OpenCV-based image processing and stitching.
- YOLOv8-based candidate-evidence detection.
- Grid-referenced and ID-labelled annotations.

**2. Evidence Integrity & Reporting**
- SHA-256 evidence hashing.
- Tamper and missing-file verification.
- Evidence manifests and audit logs.
- PDF, JSON and CSV report generation.

**3. Mobile Companion Application**
- Flutter and Dart.
- Local HTTP communication bridge.
- Evidence gallery and investigator review.
- Confirm/reject workflow for AI-identified candidates.
- GPS and time metadata, audio notes and Tamil voice dictation.

**4. Embedded Hardware Integration**
- Raspberry Pi edge processing.
- ESP32-based motor control.
- ESP-NOW communication.
- Integration with a cable-driven camera documentation platform.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python, Dart |
| Desktop | PyQt6 |
| Mobile | Flutter |
| Computer Vision | OpenCV, NumPy, YOLOv8 |
| Embedded Systems | Raspberry Pi, ESP32 |
| Communication | HTTP, ESP-NOW |
| Integrity | SHA-256 |
| Reporting | PDF, JSON, CSV |

## Engineering Principles

- Evidence integrity and traceability.
- Human-in-the-loop AI review.
- Modular system architecture.
- Structured documentation.
- Integration across software and hardware components.

## My Contribution

I led the project across problem identification, system architecture, software development, computer vision integration, mobile application development, embedded-system integration and technical documentation.

## Intellectual Property

CrimeScan is associated with Indian Patent Application Publication No. **202641105517 A**.

This repository serves as a curated engineering showcase. It does not contain the complete proprietary implementation.

## Project Status

The project has progressed through software development, system integration and hardware prototyping. Individual components and integrations are at different stages of development.

---

**Developer:** Selva Prakash M  
**Interests:** Software Engineering · Applied AI · Computer Vision · Reliable Systems

