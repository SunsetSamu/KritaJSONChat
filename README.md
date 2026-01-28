# JSON Chat Viewer Plugin for Krita

## Description

This is a custom chat viewer plugin for Krita that displays messages from a specifically formatted JSON file. The plugin is designed to work with user-created scripts that can convert any chat log (from Twitch, Discord, etc.) into the compatible JSON format. Messages are displayed in a clean, readable format from top to bottom (oldest to newest within the visible range), with visual styling.

## Features

*   **Load Custom JSON**: Load a chat log from a JSON file with a simple button click.
*   **Formatted Chat Display**: Messages are shown as `[Role] Username: Message` with color highlighting.
*   **Message Limit Control**: Set a maximum number of messages to display, showing only the most recent entries.
*   **Auto-Reload**: The viewer automatically checks for changes to the JSON file every 3 seconds and updates if modified.
*   **Session Persistence**: Remembers the last loaded file and message limit between Krita sessions.
*   **Send Bar**: Toggle a bottom bar to write and output a simple JSON message to a local file (`krita_chat_output.json`).
*   **Installation:** [Read this guide](https://github.com/EyeOdin/Pigment.O/wiki/Plugin-Instalation).

## Preview

<img src="previews/prev%20(3).png" alt="Preview" width="600">
<img src="previews/prev%20(2).png" alt="Preview" width="600">
<img src="previews/prev%20(1).png" alt="Preview" width="600">

## Usage

**Basic Viewing:**

1.  Click the **"Load Chat JSON..."** button to select your formatted JSON file.
2.  The chat messages will appear in the main display area.
3.  Use the **"Max:"** spin box to limit how many of the most recent messages are shown.

**Sending Output:**

1.  Click the **"Toggle Send"** button to show/hide the bottom input bar.
2.  Type a message in the text field.
3.  Click **"Send"** to write your message to `krita_chat_output.json`.
4.  Click the **📁 (Folder) button** to show the output JSON file.

## Compatible JSON Format

For the chat to display correctly, your JSON file must follow this exact structure. It is an object with a single key `"chat"`, whose value is an array (list) of messages. Each message is an array of three elements: `[Role, Username, Message]`.

**Key Rules:**

*   **Role**: Any string as role, like `"Mod"` or `"Sub"`. If the role is `null` or missing, no tag is displayed (e.g., `Username: Message`).
*   **Username**: The display name of the chatter.
*   **Message**: The text content of the chat message.

**Example JSON:**

```json
{
  "chat": [
    ["OP", "User1", "Hello everyone!"],
    ["Sub", "User2", "Great stream!"],
    [null, "User3", "How are you?"],
    ["OP", "User1", "Thanks for watching!"]
  ]
}
```

## Feedback & Support

This plugin is open for modification and extension. Feel free to fork and adapt it to your needs—no attribution is required.

For questions, bug reports, or discussions about implementation, please open a new issue in the project repository.