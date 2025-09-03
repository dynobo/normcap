---
hide:
  - navigation
---

# Usage

<p class="md-subtitle">A short guide for using NormCap and its most important features.</p>

## Quickstart

1. Start NormCap and wait for the pink border to appear.
1. Select a screen region with your mouse and wait for the notification or pink tray icon.
1. Paste the detected text from your clipboard into any application.
1. Access settings via the <span class="md-pink">⚙</span> menu in the top right corner.

![Screenshot of NormCap interface](./assets/screenshot.png)

## User Interface

- Access settings via the <span class="md-pink">⚙</span> icon in the top right of your primary monitor.
- Adjust recognition language(s) in settings for better accuracy.
- The icons <span class="md-pink">★</span> or <span class="md-pink">☰</span> next to the selection rectangle indicate "Parse Text" status (see below).
- Press `<esc>` to abort capture or quit NormCap.

## Detection settings

The settings menu <span class="md-pink">⚙</span> allows toggling various detection modes:

### "Detection"

- **Text**

    Extracts text from the selected area.

- **QR & Barcodes**

    Detects and decodes QR codes and barcodes in the selected area. Data from multiple codes are separated by newlines.

!!! info

    When both "Text" and "QR & Barcode" are active, "QR & Barcode" takes priority: if a code is found, text detection is skipped.

### "Post-Processing"

- **Parse Text**

    When active, the selection rectangle gets marked with a <span class="md-pink">★</span> symbol. This mode performs some formatting of the output based on certain implemented rules, which can take additional information like text position and content into account. In the first step, every rule calculates a "score" to determine the likelihood of being responsible for this type of text. In the second step, the rule which achieved the highest "score" takes the necessary actions to "transform" the input text according to its type. The following rules are currently implemented:

    | **Rule name**   | **Score heuristics**                | **Transform**                                                 |
    | --------------- | ----------------------------------- | ------------------------------------------------------------- |
    | **Single line** | Only single line detected           | Trim unnecessary whitespace                                   |
    | **Multi line**  | Multiple lines, single paragraph    | Separate with line breaks, trim whitespace per line           |
    | **Paragraph**   | Multiple line blocks or paragraphs  | Join paragraphs into single lines, separate with empty lines  |
    | **Email**       | Email address chars vs. total chars | Transform to comma-separated email list                       |
    | **URL**         | URL chars vs. total chars           | Transform to newline-separated URLs, discard other characters |

## Exemplary use cases

- Extract text from screenshots you received via email.
- Copy error messages from non-selectable UI elements.
- Retrieve information from photos.
- Capture email addresses from "crawler safe" images on the web.
- Scan QR codes in livestreams or online presentations.
- Read barcodes from product pictures.
- *... and many more!*
