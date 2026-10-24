from anki_addons_dataset.common.data_types import AiTag, AiTagDefinition, AiTagGroup


class AiTagVocabulary:
    function_tags: dict[AiTag, str] = {
        AiTag("card-creation"): "Building notes from text, words, clipboard; field auto-fill",
        AiTag("ai"): "LLM-powered features: generation, explanations, rewording, chat (ChatGPT/Gemini/DeepSeek/Ollama)",
        AiTag("import"): "From files and services: CSV, Quizlet, Notion, OneNote, Kindle, PDF, apkg",
        AiTag("export"): "To HTML/PDF/CSV/Markdown/audio, printing",
        AiTag("sync-integration"): "External apps and APIs: AnkiConnect forks, webhooks, Habitica, Yomitan, Notion, "
                                   "Obsidian",
        AiTag("scheduling"): "Intervals, ease, reschedule, delay/postpone, load balancing, answer-grade logic",
        AiTag("fsrs"): "FSRS-specific helpers",
        AiTag("review-flow"): "Review session behaviour: auto-flip, answer confirmation, bury/defer, card order, "
                              "session plans",
        AiTag("statistics"): "Graphs, heatmaps, retention, analytics, year-in-review",
        AiTag("progress-tracking"): "Progress bars, daily goals, countdowns, exam planners",
        AiTag("gamification"): "XP, pets, games, leaderboards, streaks, rewards, Pokémon",
        AiTag("motivation"): "Encouragement, affirmations, break reminders",
        AiTag("timer"): "Pomodoro, session timers, breaks",
        AiTag("note-management"): "Bulk edit, merge, find/replace, field ops, note IDs, note types",
        AiTag("tagging"): "Tag tools: hierarchical tags, clickable tags, tag shortcuts",
        AiTag("duplicates"): "Detecting and merging duplicates",
        AiTag("search"): "Browser search improvements, collection lookup",
        AiTag("filtered-decks"): "Creating and managing filtered decks",
        AiTag("deck-management"): "Deck tree, subdecks, deck options, limits",
        AiTag("leech"): "Leech handling",
        AiTag("formatting"): "Text styling, HTML cleanup, colours, Markdown in fields",
        AiTag("shortcuts"): "Keyboard shortcuts, remapping, hotkeys",
        AiTag("appearance"): "Themes, CSS, fonts, backgrounds, dark mode, blur, zoom",
        AiTag("card-templates"): "Note types and templates, special card types",
        AiTag("cloze"): "Cloze variants, overlapping cloze, cloze generators",
        AiTag("image-occlusion"): "Image occlusion",
        AiTag("quiz"): "Multiple choice, typing answers, drag-and-drop, exam simulators",
        AiTag("dictionary"): "Lookup, definitions, translation, popup dictionaries",
        AiTag("backup-maintenance"): "Backups, DB fixes, add-on management, update control",
        AiTag("bugfix-workaround"): "Fixes for Anki bugs or OS quirks (Bluetooth lag, SSL, caps lock)",
        AiTag("developer-tools"): "Debug info, inspector, config editor, add-on dev helpers",
        AiTag("accessibility"): "Readability, larger text, remote control, controllers",
    }
    status_tags: dict[AiTag, str] = {
        AiTag("no-description"): "Empty, test or placeholder addons (\"hello world\", \"up to date\", bare numbers)",
        AiTag("obsolete"): "Built into Anki now, or stated as no longer working",
        AiTag("fork-or-reupload"): "\"Fixed by Shige\", forks, ports to 2.1",
        AiTag("paid"): "Patreon-only, \"Not Free\", Pro tiers, subscriptions",
        AiTag("service-client"): "Companion to a commercial service (Migaku, Kimchi Reader, IvyTutoring, Picmonic)",
        AiTag("mobile-compatible"): "Works on AnkiDroid or AnkiMobile through templates",
        AiTag("beta"): "Self-declared alpha, beta or WIP",
    }

    @staticmethod
    def definitions() -> list[AiTagDefinition]:
        return [*AiTagVocabulary.__group(AiTagVocabulary.function_tags, AiTagGroup("function")),
                *AiTagVocabulary.__group(AiTagVocabulary.status_tags, AiTagGroup("status"))]

    @staticmethod
    def __group(tags: dict[AiTag, str], group: AiTagGroup) -> list[AiTagDefinition]:
        return [AiTagDefinition(name, group, description) for name, description in tags.items()]
