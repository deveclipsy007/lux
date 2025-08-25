CREATE TABLE `agents` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`name` text NOT NULL,
	`specialization` text,
	`instructions` text,
	`status` text DEFAULT 'inactive' NOT NULL,
	`created_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `conversations` (
	`chat_id` text PRIMARY KEY NOT NULL,
	`instance_id` integer NOT NULL,
	`agent_id` integer NOT NULL,
	`contact_number` text NOT NULL,
	`created_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`instance_id`) REFERENCES `whatsapp_instances`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`agent_id`) REFERENCES `agents`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_conversations_instance` ON `conversations` (`instance_id`);--> statement-breakpoint
CREATE INDEX `idx_conversations_agent` ON `conversations` (`agent_id`);--> statement-breakpoint
CREATE TABLE `messages` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`instance_id` integer NOT NULL,
	`agent_id` integer NOT NULL,
	`from_number` text,
	`to_number` text,
	`content` text,
	`created_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`instance_id`) REFERENCES `whatsapp_instances`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`agent_id`) REFERENCES `agents`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_messages_instance` ON `messages` (`instance_id`);--> statement-breakpoint
CREATE INDEX `idx_messages_agent` ON `messages` (`agent_id`);--> statement-breakpoint
CREATE TABLE `system_events` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`event_type` text NOT NULL,
	`source` text,
	`target_id` integer,
	`data` text,
	`created_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_system_events_type` ON `system_events` (`event_type`);--> statement-breakpoint
CREATE TABLE `whatsapp_instances` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`agent_id` integer NOT NULL,
	`status` text DEFAULT 'inactive' NOT NULL,
	`qr_code` text,
	`phone_number` text,
	`created_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` integer DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`agent_id`) REFERENCES `agents`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_whatsapp_instances_agent` ON `whatsapp_instances` (`agent_id`);