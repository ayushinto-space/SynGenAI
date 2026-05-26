# SynGenAI | AI-Powered Synthetic Data Generator

SynGenAI is a dynamic, AI-powered synthetic data generation tool built with Streamlit and Google GenAI SDK. Instead of using rigid templates it utilizes `gemini-2.5-flash` to architect custom relational database schemas on the fly based on natural language user prompts further it populates the schema to generate realistic mock datasets using `Faker` and `pandas`.

## 🚀 Features

- **Dynamic Schema Engineering:** Ask for any domain (e.g. "Hospital system with laboratory blood tests") and the AI builds a custom JSON blueprint.
- **Relational Integrity:** Automatically links parent and child tables via relational keys and enforces temporal integrity.
- **Custom Sizing:** Adjust sliders to generate anywhere from a few rows to thousands of mock records as per user needs.
- **Instant Export:** Review a 15-row preview directly in the UI and download the complete tables instantly as CSV files.

## 🛠️ Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ayushinto-space/SynGenAI.git
cd SynGenAI
