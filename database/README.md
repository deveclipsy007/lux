# Database Schema

This directory contains the database schema and repository utilities used by the project.

## Tables

### `agents`
Represents autonomous agents that interact with users. Each agent can own multiple WhatsApp instances.

### `whatsapp_instances`
Stores WhatsApp Web sessions linked to an agent. An instance belongs to a single agent and holds metadata such as QR codes and phone numbers.

### `messages`
Persists inbound and outbound messages exchanged through a specific instance. Messages reference both the sending agent and the instance on which they were transmitted.

### `conversations`
Tracks active chats between an agent and a contact phone number for a given instance. A conversation is uniquely identified by `chat_id`.

### `system_events`
Generic event log used for auditing or debugging. Events can reference other entities through the `target_id` field.

## Relationships

- An `agent` has many `whatsapp_instances`, `messages`, and `conversations`.
- A `whatsapp_instance` has many `messages` and `conversations`.
- `messages` and `conversations` reference both `agents` and `whatsapp_instances` via foreign keys.

## Naming Conventions

- Table names use **snake_case** plural nouns (e.g., `system_events`).
- Column names also follow snake_case.
- Timestamp columns are named `created_at` and `updated_at` for consistency.

Repositories that encapsulate access to these tables are available in [`database/repositories`](./repositories).
