---
title: "`discord`: bots and webhooks over `std/http` and `std/ws`"
description: "A Discord library for bots and webhooks: payload builders that emit JSON, a gateway loop that identifies, heartbeats and resumes, webhooks by URL, and every opcode, close code and intent the raw path needs."
isPublished: true
tags: "library, networking"
---
The library's own copy of this page is [`docs/discord.md`](https://homelabone.xenoo.dev/gittea/Juniper/fpl/src/branch/main/docs/discord.md)
in the [fpl repository](https://homelabone.xenoo.dev/gittea/Juniper/fpl).

A Discord library with two halves and one file. The easy path is a bot or a
webhook that works: a `Bot` value, payload builders that emit JSON, a gateway
loop that identifies, heartbeats, resumes and reconnects, and webhook posting by
URL or by token. The raw path is everything the easy path uses, exported: every
opcode, close code, intent and component type as a named constant, the payload
accessors, the REST request builders, the `Session` state machine on its own, and
`JsonObject` for a field this library does not model.

Nothing is reachable only through the convenient path. The loop the easy path
runs is `gateway_loop`, and the same loop written by hand from `Session`,
`heartbeat_payload` and `socket_readable` is in "The raw path" below.

**Three capability domains, and all three are on the caller's line.** A module
holds only what its importer granted, and this library dials Discord itself, so
the grant has to be real: `caps(net = [])` would satisfy the compiler and then
deny every call at runtime.

| Domain | What it costs, and why |
| --- | --- |
| `net` | `std/http` for the REST API, `std/ws` for the gateway socket |
| `rand` | `std/ws` needs it for the handshake key and the masking key of every frame (RFC 6455 requires both to be unpredictable) |
| `time` | the heartbeat interval op 10 HELLO carries is a duration, and the reconnect backoff is a wait: `time.now_mono_ns` and `time.sleep_ms` are v1's only clock, and `plan/mk9-memory-model.md` names `wait_readable` plus a sleep as the single-threaded loop's timer |

This library's own `impl` lines grant each shipped module the wildcard,
`net = ["*"]` for `std/http` and `std/ws` and `time = []` for `std/time`, because
it does not know which host a caller points it at: Discord's own endpoints, a
local mock, or a TLS terminator in front. Capability patterns are static text
and a module can delegate less than it holds, never more, so the caller's line
has to hold the wildcard too:

```toml
[dependencies]
discord = "Juniper/fpl/discord"
```

```kelp
impl "deps/discord/lib" caps(*)
```

`caps(*)` is that clause in one line: it delegates the whole resource of every
domain the importing module holds. A program's entry module holds all six, so it
is the line to write here. The spelled-out form names the three domains one by
one, `caps(net = ["*"], rand = [], time = [])`, and says the same thing.

**A narrower grant cannot import this library.** Delegation may be smaller than
what the caller holds, never larger, so `caps(net = ["discord.com:443"])` on this
import does not build: the refusal names the pattern this module delegates and
the one it was given. A caller who wants the socket to hold one host does not
import `discord` at all. The narrow alternative is the gateway loop written by
hand against `std/ws`:

```kelp
impl "std/ws" caps(net = ["gateway.discord.gg:443"], rand = [])
```

with the frames, the sequence bookkeeping and the payload JSON the caller's own.
That is the same loop "The raw path" below shows, minus the library.

**TLS.** Discord is `https://` and `wss://` end to end, and v1 has no TLS
(`MISSING-XkcSp`): `std/http` refuses `https` and `std/ws` refuses `wss`, each
with a message naming TLS. So the REST base URL and the gateway URL are
configuration, defaulting to Discord's real endpoints, and **the defaults are not
reachable from v1**. Point them at a plain `http://`/`ws://` endpoint (a local
one, or a TLS terminator in front of you) and nothing else changes:

```kelp
var bot = discord.bot_with_intents("TOKEN", discord.intents_all())
bot.set_api_base("http://127.0.0.1:8099")
bot.set_gateway_url("ws://127.0.0.1:8098/?v=10&encoding=json")
```

`discord.run_gateway` refuses a TLS gateway URL itself, through
`discord.gateway_endpoint(bot)`, with a message that says so before `std/ws`
would. A REST call against `https` panics with `std/http`'s
own `https` message.

## The constants

Everything numeric Discord names is a named constant, so nothing in a payload is
a bare number:

| Family | Examples |
| --- | --- |
| `OP_*` | `OP_HELLO`, `OP_DISPATCH`, `OP_HEARTBEAT`, `OP_IDENTIFY`, `OP_RESUME`, `OP_RECONNECT`, `OP_INVALID_SESSION`, `OP_HEARTBEAT_ACK` |
| `CLOSE_*` | `CLOSE_NORMAL`, `CLOSE_AUTHENTICATION_FAILED`, `CLOSE_SESSION_TIMED_OUT`, `CLOSE_DISALLOWED_INTENTS` |
| `INTENT_*` | the table under "Intents" |
| `MESSAGE_FLAG_*` | `MESSAGE_FLAG_EPHEMERAL`, `MESSAGE_FLAG_SUPPRESS_NOTIFICATIONS`, `MESSAGE_FLAG_SUPPRESS_EMBEDS` |
| `COMPONENT_*` | `COMPONENT_ACTION_ROW`, `COMPONENT_BUTTON`, `COMPONENT_STRING_SELECT`, `COMPONENT_TEXT_INPUT`, and the four entity selects |
| `BUTTON_*` | `BUTTON_PRIMARY`, `BUTTON_SECONDARY`, `BUTTON_SUCCESS`, `BUTTON_DANGER`, `BUTTON_LINK` |
| `TEXT_INPUT_*` | `TEXT_INPUT_SHORT`, `TEXT_INPUT_PARAGRAPH` |
| `INTERACTION_*` | `INTERACTION_PING`, `INTERACTION_APPLICATION_COMMAND`, `INTERACTION_MESSAGE_COMPONENT`, `INTERACTION_AUTOCOMPLETE`, `INTERACTION_MODAL_SUBMIT` |
| `CALLBACK_*` | `CALLBACK_PONG`, `CALLBACK_CHANNEL_MESSAGE_WITH_SOURCE`, `CALLBACK_DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`, `CALLBACK_UPDATE_MESSAGE`, `CALLBACK_DEFERRED_UPDATE_MESSAGE`, `CALLBACK_AUTOCOMPLETE_RESULT`, `CALLBACK_MODAL` |
| `COMMAND_*`, `OPTION_*` | `COMMAND_CHAT_INPUT`, `COMMAND_USER`, `COMMAND_MESSAGE` and `OPTION_STRING` through `OPTION_ATTACHMENT` |
| `CHANNEL_*` | the channel types a channel select takes, `CHANNEL_GUILD_TEXT` to `CHANNEL_GUILD_MEDIA` |
| `STATUS_*` | `STATUS_ONLINE`, `STATUS_IDLE`, `STATUS_DND`, `STATUS_INVISIBLE`, for `presence_payload` |
| `COLOR_*` | Discord's palette, plus `rgb(r, g, b)` |
| `DEFAULT_*`, `API_VERSION`, `SNOWFLAKE_EPOCH_MS` | `DEFAULT_API_BASE`, `DEFAULT_GATEWAY_URL`, `DEFAULT_USER_AGENT`, `DEFAULT_WEBHOOK_BASE`, `DEFAULT_PROPERTIES` |

## The easy path

### The smallest bot

```kelp
impl "deps/discord/lib" caps(*)

fun on_command(i: &discord.Interaction, bot: &discord.Bot) {
    val reply = discord.reply(discord.message_text("pong"))
    val body = reply.compact()
    print(discord.respond_interaction(bot, i, body.as_str()).status)
}

fun main() {
    var bot = discord.bot_with_intents("TOKEN", discord.intents_all())
    var hs = discord.handlers()
    hs.set_command(fun(i: &discord.Interaction, b: &discord.Bot) { on_command(i, b) })
    discord.run_gateway(bot, hs)
}
```

That is the whole bot: the loop dials, reads HELLO, identifies with the intents,
answers heartbeats with the last dispatch's sequence, resumes after a reconnect
the server asked for, backs off between attempts, and closes for good on a code
that says retrying cannot work. With Discord's defaults it panics on the TLS
gateway URL, as above; with a `ws://` gateway it runs unchanged.

Every handler is optional and the default does nothing:

| Setter | Closure |
| --- | --- |
| `hs.set_ready` | `(payload: &GatewayPayload, bot: &Bot)` |
| `hs.set_command` | `(i: &Interaction, bot: &Bot)` for an application command |
| `hs.set_component` | `(i: &Interaction, bot: &Bot)` for a message component |
| `hs.set_modal` | `(i: &Interaction, bot: &Bot)` for a modal submit |
| `hs.set_autocomplete` | `(i: &Interaction, bot: &Bot)` for an autocomplete |
| `hs.set_event` | `(payload: &GatewayPayload, bot: &Bot)` for everything else |
| `hs.set_close` | `(code: u16, bot: &Bot)` |

A handler takes the bot as an argument rather than capturing it: a capture is a
move, so a closure over `bot` would take the bot away from the caller who still
has to pass it to `run_gateway`. The defaults are `ignore_payload`,
`ignore_interaction` and `ignore_close`, which are public, so a handler can be
set back to a no-op as easily as it was set.

### The smallest webhook post

```kelp
impl "deps/discord/lib" caps(*)

fun main() {
    val hook = discord.webhook_default("WEBHOOK_ID", "WEBHOOK_TOKEN")
    var m = discord.message_text("deploy finished")
    print(discord.post_webhook(hook, m, false, "").status)
}
```

`wait` asks Discord to answer with the message it created, and `thread_id`
posts into a thread; both are query parameters of the webhook's own endpoint.
`discord.post_webhook_url(url, payload_json)` is the same thing when the caller
has only the URL as text, and `discord.parse_webhook_url` turns a URL into the
id, the token and the base.

### Replying to an interaction

`reply`, `reply_deferred`, `update_message`, `update_deferred`, `respond_modal`,
`respond_pong`, `autocomplete_choice` and `autocomplete_choices` build the
callback body, and
`interaction_response(kind, data)` is the one underneath them for a callback type
they do not cover. The callback itself carries its authority in the URL, so it
needs no `Authorization` header.

```kelp
// an ephemeral reply, the one flag a bot sets most
var m = discord.message_text("only you can see this")
m.set_ephemeral(true)
val body = discord.reply(m).compact()
print(discord.respond_interaction(bot, i, body.as_str()).status)

// a deferred reply, because 3 seconds is not always enough
val deferred = discord.reply_deferred(false).compact()
print(discord.respond_interaction(bot, i, deferred.as_str()).status)
```

## The raw path

Everything the easy path does is a value the caller can build, keep, print or
send. The same bot, driven by hand:

```kelp
impl "std/ws"
impl "std/time"
impl "deps/discord/lib" caps(*)

fun main() {
    var bot = discord.bot_with_intents("TOKEN", discord.intents_all())
    val ep = discord.split_url("ws://127.0.0.1:8098/?v=10&encoding=json")
    if let Ok(e) = ep {
        val target = e.path_and_query()
        var conn = ws.connect(e.host.as_str(), e.port, target.as_str())
        var session = discord.session()
        var hs = discord.handlers()
        var going = true
        while going {
            val now = discord.now_ms()
            if session.heartbeat_due(now) {
                val beat = session.next_heartbeat_payload()
                conn.send_text(beat.as_str())
                session.note_heartbeat(now)
            }
            var readable = conn.start < conn.buf.len()
            if !readable {
                readable = discord.socket_readable(conn.fd, 250)
            }
            if readable {
                when conn.recv() {
                    Text(t) -> {
                        val parsed = discord.parse_gateway_payload(t.as_str())
                        if let Ok(p) = parsed {
                            if p.op == discord.OP_HELLO {
                                session.apply_hello(p.data.get_int("heartbeat_interval"))
                                val hello_reply = session.identify_or_resume(bot)
                                conn.send_text(hello_reply.as_str())
                            } else if p.op == discord.OP_DISPATCH {
                                session.apply_dispatch(p.seq)
                                discord.dispatch_payload(p, hs, bot)
                            }
                        }
                    }
                    Ping(d) -> conn.pong(d)
                    Close(code, why) -> {
                        print(discord.close_code_name(code))
                        going = false
                    }
                    else -> {
                    }
                }
            }
        }
    }
}
```

That is the same loop with the caller's own timer: `discord.now_ms` is the
clock, `discord.socket_readable` is the poll, and every decision is a `Session`
method the caller can also test without a socket.

The same webhook post, request by request:

```kelp
val hook = discord.webhook_default("WEBHOOK_ID", "WEBHOOK_TOKEN")
val m = discord.message_text("deploy finished")
val body = m.text()
val path = hook.post_path(false, "")
val req = discord.webhook_request(hook, "POST", path.as_str(), body.as_str())
print(req.method.as_str())     // POST
print(req.url.as_str())        // https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
print(req.headers.len())       // 2: User-Agent and Content-Type, and no Authorization
val signed = discord.with_header(req, "X-Audit-Log-Reason", "cleanup")
```

`with_header` takes the request with `move` and hands the changed one back, and
`req.headers.push(http.Header(name = ..., value = ...))` is the other way to add
one. Every header the library sets is set in `request_at`, which is public.

| Helper | Returns |
| --- | --- |
| `split_url(url)` | `Result<Endpoint, ParseErr>`: `scheme`, `host`, `port`, `path`, `query`, `tls` |
| `e.path_and_query()`, `e.url()` | the path with its query, and the URL back as text |
| `needs_tls(scheme)` | whether a scheme needs TLS, which v1 has not got |
| `escape_uri(text)` | one query value or path segment, percent-encoded |
| `tls_message(what, url)` | the refusal this library writes for a `wss://` or `https://` URL |

## Intents

`discord.intents_all()`, `discord.intents_unprivileged()` (everything Discord
will accept without a portal approval), `discord.intents()` (none) and
`discord.intents_of(bits)` build one; `with`, `without` and `has` change and ask;
`intents.bits` is the number.

| Constant | Bit | Constant | Bit |
| --- | --- | --- | --- |
| `INTENT_GUILDS` | 1 | `INTENT_GUILD_MESSAGES` | 512 |
| `INTENT_GUILD_MEMBERS` | 2 | `INTENT_GUILD_MESSAGE_REACTIONS` | 1024 |
| `INTENT_GUILD_MODERATION` | 4 | `INTENT_GUILD_MESSAGE_TYPING` | 2048 |
| `INTENT_GUILD_EMOJIS_AND_STICKERS` | 8 | `INTENT_DIRECT_MESSAGES` | 4096 |
| `INTENT_GUILD_INTEGRATIONS` | 16 | `INTENT_DIRECT_MESSAGE_REACTIONS` | 8192 |
| `INTENT_GUILD_WEBHOOKS` | 32 | `INTENT_DIRECT_MESSAGE_TYPING` | 16384 |
| `INTENT_GUILD_INVITES` | 64 | `INTENT_MESSAGE_CONTENT` | 32768 |
| `INTENT_GUILD_VOICE_STATES` | 128 | `INTENT_GUILD_SCHEDULED_EVENTS` | 65536 |
| `INTENT_GUILD_PRESENCES` | 256 | `INTENT_GUILD_AUTO_MODERATION_CONFIGURATION` | 262144 |
| | | `INTENT_GUILD_AUTO_MODERATION_EXECUTION` | 524288 |

`intents.names()` is the named flags a bitfield holds, in bit order. The default
for `discord.bot` is `intents_unprivileged()`, because an intent Discord has not
approved is a close code 4014 rather than a bot that works.

## Snowflakes

Ids are 64-bit: 42 bits of milliseconds since Discord's epoch, then a worker id,
a process id and a counter.

| Function | Returns |
| --- | --- |
| `snowflake(id)` | `Snowflake`, with `ms`, `worker`, `process_id`, `increment` |
| `snowflake_ms(id)` / `snowflake_worker(id)` / `snowflake_process(id)` / `snowflake_increment(id)` | one part each |
| `snowflake_of_str(text)` | `Option<u64>`, for the JSON string Discord sends |
| `snowflake_text(id)` | the decimal spelling |
| `snowflake_after_epoch(ms)` | a minimal id at that offset, for a local test server |
| `snowflake_newer(a, b)` / `snowflake_age_ms(id, now_ms)` | comparison and age |

## JSON

A folder here must stand alone, so this library cannot `impl` the `json` folder:
the same reason `httpx` carries its own base64. The copy is small, and it is
public because the raw path wants it: every payload accessor returns a `Json`,
and `JsonObject` is how a caller adds a field the library does not model.

| Item | Notes |
| --- | --- |
| `Json` | `Null`, `Bool`, `Int`, `Float`, `Str`, `Array`, `Object` |
| `jstr`, `jint`, `jbool`, `jfloat`, `jstring`, `jarr`, `jobj`, `jnull` | constructors |
| `object()`, `o.add`, `o.set`, `o.add_str`, `o.add_int`, `o.add_bool`, `o.add_float`, `o.add_null`, `o.add_text_value`, `o.json()`, `o.text()` | the object builder, and `set` replaces a key that is already there |
| `parse_json` / `parse_json_or_null` | `Result<Json, ParseErr>`, and `Null` on failure |
| `v.get(key)`, `v.pick(key)`, `v.at(i)`, `v.len()`, `v.has(key)`, `v.keys()`, `v.str_list()` | lookup; `get` panics, `pick` returns `Null` |
| `v.as_str()`, `v.as_i64()`, `v.as_u64()`, `v.as_f64()`, `v.as_bool()`, `v.as_items()`, `v.kind()`, `v.is_*()` | readers; the readers panic on the wrong type |
| `v.text_or`, `v.int_or`, `v.bool_or`, `v.get_text`, `v.get_int`, `v.get_bool` | readers that never panic |
| `v.compact()`, `v.pretty()`, `v.pretty_with(n)`, `v.clone()` | text in and values out |
| `quote(s)`, `escape_json(view, out)`, `write_into(v, out)`, `float_text(x)` | the writer's pieces, for a caller building payload text by hand |

## Message payloads

`message()` is empty, `message_text(content)` is not, and every field is a setter.
`m.text()` is the JSON text, `m.json()` is the same tree.

| Setter | Field |
| --- | --- |
| `set_content`, `add_embed`, `add_row` | `content`, `embeds`, `components` |
| `set_flags`, `add_flag`, `set_ephemeral(on)` | `flags`, and `MESSAGE_FLAG_*` are the bits |
| `set_tts`, `set_username`, `set_avatar_url`, `set_thread_name`, `set_nonce` | the rest of the payload |
| `set_allowed_mentions` | `allowed_mentions`, built by `mentions_none`, `mentions_parse`, `mentions_users`, `mentions_roles` |
| `set_extra(key, value)` | any field this library does not model, merged last so it can also override |

A message is a value: build it, keep it, print `text()`, or hand the same value
to `send_message`, `post_webhook` or `reply`. Nothing is global. Every builder
here is a plain `datac` value: `Message`, `Embed`, `SelectOption`, `StringSelect`,
`EntitySelect`, `TextInput`, `Modal`, `Command`, `CommandOption`, `JsonObject`,
`Session`, `Handlers`, `Bot` and `Webhook`.

## Embeds

`embed(title)`, `embed_of(title, description)`, `embed_colored(title, desc, color)`
then `set_description`, `set_url`, `set_color`, `set_timestamp`, `set_footer`,
`set_image`, `set_thumbnail`, `set_author`, `add_field(name, value, inline)`,
`clear_fields`, and `e.json()` / `e.text()`. `embed_field` builds one field as a
value, and `rgb(r, g, b)` is Discord's 24-bit colour. The named `COLOR_*`
constants are Discord's own palette. An empty string means "not set", which is
what makes one small `json` write only the fields the caller chose.

## Components and modals

Every component is a value with every field Discord defines, and `json` writes
only the fields that were set.

| Item | Notes |
| --- | --- |
| `button(custom_id, label, style)`, `button_primary`, `button_secondary`, `button_success`, `button_danger`, `button_link`, `button_with_emoji`, `button_disabled(b)` | `BUTTON_PRIMARY` to `BUTTON_LINK` are the styles |
| `select_option(label, value)`, `select_option_of(...)`, `select_option_selected(...)` | one option of a string select |
| `string_select(custom_id)` then `add_option`, `set_placeholder`, `set_min_values`, `set_max_values`, `set_disabled` | `COMPONENT_STRING_SELECT` |
| `entity_select(custom_id, component_type)` then `add_channel_type`, `add_default` | user, role, mentionable and channel selects |
| `action_row(children)`, `row_of(one)` | a row; it holds at most five buttons or one select |
| `text_input(custom_id, label)`, `text_input_paragraph(...)` | `TEXT_INPUT_SHORT`, `TEXT_INPUT_PARAGRAPH` |
| `modal(custom_id, title)` then `add_row`, `add_input`, `m.text()` | `discord.respond_modal(m)` is the callback |

`add_input` wraps the text input in a row, which is the step a caller would
otherwise forget. A component this library does not model is built with
`object()` and put in a row with `action_row`: `COMPONENT_*` are the numbers.

## Command registration

`command(name, description)`, `user_command(name)` and `message_command(name)`;
`options` are built from `option_string`, `option_integer`, `option_number`,
`option_boolean`, `option_user`, `option_channel`, `option_role`,
`option_mentionable`, `option_attachment`, `option_ranged`,
`option_integer_ranged`, `subcommand` and `subcommand_group`, each with
`add_choice` (`choice`, `choice_int`, `choice_number`), `add_nested` for a
subcommand's own options, `add_channel_type`, and `add_option` on the command.
`c.set_default_member_permissions(bits)`, `c.set_dm_permission(false)` makes it
guild only, and `c.set_nsfw(true)`. `c.json()` is the body of the registration
request and `c.text()` is that body as text, which is what
`register_global_command` and `register_guild_command` send.

`dm_permission` is written on every registration: a field the library never
writes is a control the caller does not have.

## Interactions

`parse_interaction(text)` and `interaction_from(json)` produce an `Interaction`
with `id`, `token`, `kind`, `application_id`, `command_name`, `custom_id`,
`component_type`, `values`, `user_id`, `user_name`, `guild_id`, `channel_id` and
`payload` (the whole object, so nothing Discord sent is dropped).

| Reader | Notes |
| --- | --- |
| `i.option(name)` | the value, following `data.options` and one level of subcommand options; `Null` when absent |
| `i.option_text` / `i.option_int` / `i.option_bool` | with a fallback |
| `i.field(custom_id)` | a modal's text input value |
| `interaction_kind_name(kind)` | `ping`, `application_command`, `message_component`, `autocomplete`, `modal_submit` |
| `option_value(data, name)` | the same lookup over a bare payload |

## Signatures: the Ed25519 gap

Discord signs every interaction webhook with Ed25519: the signature in
`X-Signature-Ed25519`, the timestamp in `X-Signature-Timestamp`, and the signed
message is the timestamp bytes followed by the raw body.

**v1 has no Ed25519, so this library cannot check a signature and does not
pretend to.** It hands over the three raw pieces:

```kelp
val sig = discord.interaction_signature(headers, body)   // body is moved in
print(sig.signature)      // X-Signature-Ed25519, verbatim
print(sig.timestamp)      // X-Signature-Timestamp, verbatim
print(discord.signed_message(sig))   // timestamp bytes + body, as Bytes
```

and `verify_with(sig, verifier)` is the seam: the caller's verifier is called and
its answer is returned. `header_value(headers, name)` is the case-insensitive
lookup both use, for a caller reading any other header. `is_signed(sig)` only says whether both headers were
present. Until an Ed25519 implementation exists, the honest deployment is a
reverse proxy in front that verifies the signature and forwards only what it
verified; the pieces above are what the proxy and the bot have to agree on.

## Rate limits

`std/http` has no 429 handling and no `Retry-After` handling, and that is an open
item. **This library does not retry either.** It parses the headers and hands
them back:

| Item | Returns |
| --- | --- |
| `rate_limit(resp)` | `RateLimit`: `ok`, `bucket`, `limit`, `remaining`, `reset_after_ms`, `retry_after_ms`, `global`, `scope` |
| `is_rate_limited(resp)` | `resp.status == 429` |
| `retry_after_ms(resp)` | `Retry-After` in milliseconds, or `X-RateLimit-Reset-After` |
| `seconds_text_to_ms(text)` | the decimal-seconds parser both use, rounding up |

The caller sleeps with `time.sleep_ms` and decides whether to retry, which is
the only place that decision can be made correctly: a library cannot know
whether the request was idempotent.

## REST

`Bot` carries the token, the scheme (`Bot`, or `Bearer` for a user token), the
API base, the gateway URL, the user agent, the intents, the presence and the
shard, and every one of them is settable.

| Item | Notes |
| --- | --- |
| `bot(token)`, `bot_with_intents(token, flags)` | Discord's base URL, `Bot` scheme, unprivileged intents by default |
| `set_api_base`, `set_gateway_url`, `set_user_agent`, `set_auth_scheme`, `set_intents`, `set_intent_bits`, `set_presence`, `set_properties`, `set_shard` | the controls |
| `request_at(base, method, path, body, content_type, authorization, user_agent)` | the one builder every request goes through |
| `request`, `json_request`, `get_request`, `delete_request` | the same, with the bot's token and user agent |
| `webhook_request(w, method, path, body)` | no `Authorization` at all |
| `with_header(req, name, value)` | one more header, on a request taken with `move` |
| `send_request(bot, req)`, `send_json(bot, method, path, body)`, `send_at(base, method, path, body)` | the three ways to send |
| `channel_messages_path`, `channel_message_path`, `channel_path`, `global_commands_path`, `global_command_path`, `guild_commands_path`, `interaction_callback_path`, `interaction_webhook_base`, `original_response_path`, `DM_CHANNELS_PATH`, `CURRENT_USER_PATH`, `GATEWAY_ENDPOINT_PATH` | the paths, so a caller can build their own request for an endpoint this library does not have a helper for |

`send_message`, `send_message_json`, `edit_message`, `delete_message`,
`get_message`, `get_channel`, `get_current_user`, `get_gateway_endpoint`,
`create_dm_channel`, `register_global_command`, `register_global_command_json`,
`list_global_commands`, `delete_global_command`, `register_guild_command`,
`respond_interaction`, `respond_interaction_to`, `edit_interaction_reply`,
`delete_interaction_reply` and `followup_message` are those paths with a
`Response` at the end. A non-2xx
status is not a panic; it is a `Response` with that status, and `rate_limit(resp)`
says what to do about it.

## Webhooks

`webhook(id, token, base)`, `webhook_default(id, token)`, and
`parse_webhook_url(url)` for a URL as text. `base` is everything up to and
including `webhooks`; Discord's is `https://discord.com/api/webhooks` and
`DEFAULT_WEBHOOK_BASE` is that string, so a local endpoint is
`http://127.0.0.1:8080/api/webhooks`.

| Item | Notes |
| --- | --- |
| `w.post_path(wait, thread_id)` | the path and the two query parameters |
| `w.message_path(message_id)` | the path of one message |
| `post_webhook(w, message, wait, thread_id)`, `post_webhook_text(w, content)` | post, with a built payload or with text |
| `post_webhook_json(w, payload_json, wait, thread_id)`, `post_webhook_url(url, payload_json)` | post the JSON the caller already has |
| `edit_webhook_message`, `delete_webhook_message`, `get_webhook_message` | the rest of a webhook's surface |
| `webhook_url_of(w)` | the URL back as text |

There is nothing to authenticate: the id and the token in the path are the
authority, and no `Authorization` header is sent.

## The gateway

`GatewayPayload` is one parsed frame: `op`, `event_name`, `seq`, `data`, with all
of `Json` behind `data`. `parse_gateway_payload(text)` and
`gateway_payload_from(json)` build one; `dispatch_payload(p, hs, bot)` routes it
the way the loop does.

Every payload the client sends has a builder, and each returns JSON text:

| Builder | Opcode |
| --- | --- |
| `heartbeat_payload(seq)`, `heartbeat_payload_unsequenced()` | 1; `session_seq_text(seq)` is the `null`-before-the-first-dispatch spelling |
| `identify_payload(token, intents, properties_json)`, `identify_payload_sharded(...)`, `identify_payload_with_presence(...)`, `bot_identify_payload(bot)`, `properties(os, browser, device)` | 2 |
| `presence_payload(status, activities_json, afk, since)` | 3 |
| `update_voice_state_payload(guild_id, channel_id, self_mute, self_deaf)` | 4 |
| `resume_payload(token, session_id, seq)` | 6 |
| `request_members_payload(guild_id, query, limit)` | 8 |
| `request_soundboard_sounds_payload(guild_ids)` | 31 |

`opcode_name(op)` and `close_code_name(code)` are the names for a log line, and
`close_code_reconnect(code)` and `close_code_clears_session(code)` are Discord's
own rules: 4004 (a bad token) and 4010 to 4014 (a bad shard, a bad API version,
an intent the application may not use) do not reconnect, and 4007, 4009 and 4004
say the next connection has to identify rather than resume.

`Session` is the state, and every transition is a method:

| Item | Notes |
| --- | --- |
| `session()` | nothing seen yet, sequence -1 |
| `apply_hello(interval_ms)`, `apply_ready(session_id, resume_url, guild_count)`, `apply_dispatch(seq)`, `apply_resumed()`, `apply_invalid_session(resumable)`, `reset()` | the transitions |
| `heartbeat_due(now_ms)`, `heartbeat_late(now_ms)` | when to send, and when the connection is a zombie because a heartbeat went unanswered |
| `note_heartbeat(now_ms)`, `note_ack()` | the bookkeeping |
| `next_heartbeat_payload()`, `identify_or_resume(bot)` | what to send |
| `can_resume()`, `has_sequence()` | whether a resume is possible |
| `reconnect_delay_ms(attempt)` | one second, doubling, capped at a minute |

Nothing in `Session` touches a socket, so the decisions of a loop can be tested
without one.

`gateway_loop(bot, hs, max_dispatches)` is the loop itself and returns how many
dispatches it handled; `max_dispatches` above zero stops after that many (which
is what a test or a one-shot bot wants) and zero means "until a close code says
stop". `run_gateway(bot, hs)` is the same call with the budget off.

Two of its pieces are public on their own, for a loop that wants to keep its own
structure:

| Piece | Notes |
| --- | --- |
| `one_connection(bot, hs, session, max_dispatches, handled)` | one connection start to finish; returns a `SessionOutcome` with the close `code`, the `handled` count and a `reason` |
| `handle_text(bot, hs, session, text, handled, max_dispatches)` | one text frame through the state machine; returns a `TextStep` with the outbound payload to send, if any, and whether the loop should stop |

## Example

An excerpt of the pure half of the library's own demo output: the message
payload, the parsed interaction, the gateway builders, the session decisions, the
rate-limit parse and the request shape. Every line of that program is
deterministic, so this excerpt is too.

```
{"content":"hello","embeds":[{"title":"Deploy","description":"It worked","color":5763719,"footer":{"text":"kelp"},"fields":[{"name":"host","value":"thinkbox","inline":true}]}],"components":[{"components":[{"custom_id":"btn","label":"Click","style":1,"type":2}],"type":1}],"flags":64,"allowed_mentions":{"parse":[]}}
111
application_command
echo
ada
3
{"op":1,"d":null}
{"op":1,"d":42}
{"op":2,"d":{"token":"TOKEN","intents":1,"properties":{"os":"linux","browser":"kelp","device":"kelp"}}}
{"op":6,"d":{"token":"TOKEN","session_id":"sess-1","seq":42}}
917501
true
guilds,guild_messages
abc
5
0
1250
2500
true
user
41250
true
7
3
false
true
true
false
1000
16000
60000
POST
https://discord.com/api/v10/channels/123/messages
3
User-Agent
Authorization
Bot TOKEN
Content-Type
```

## Notes

- **The gateway loop does connect, and it is tested against a loopback gateway:**
  the WebSocket handshake, HELLO, IDENTIFY, READY, two heartbeats carrying the
  sequence from the last dispatch, an INTERACTION_CREATE answered over REST,
  CLOSE 4000, a reconnect, and an op 6 RESUME carrying the session id and the
  sequence. The REST half is tested the same way, against a loopback endpoint
  that answers with Discord's rate-limit headers.
- **TLS is not here** (`MISSING-XkcSp`). The defaults name Discord's real
  endpoints and are unreachable from v1; the code is the same against a local
  `http://`/`ws://` endpoint. Nothing shells out to `curl` and nothing pretends.
- **Ed25519 verification is not here.** The raw signature, the timestamp and the
  body are handed over, `verify_with` is the seam, and a reverse proxy is the
  honest deployment until `std/crypto` exists.
- **No retries and no rate-limit waiting.** `rate_limit(resp)` is a value; the
  decision and the sleep are the caller's.
- **`ws.try_connect` is the dial that does not end the loop**: where
  `ws.connect` panics when the dial fails, `ws.try_connect` returns `WsErr.Dial`
  with the refused connection's reason, so a redial after a dial that fails
  (a wrong host, a refused connection) can survive instead of ending the process.
- **A resume lands on the configured gateway URL**, not on the
  `resume_gateway_url` Discord sends in READY: that URL is `wss://` in practice
  and therefore unreachable from v1, and a resume against a local endpoint has to
  go where the caller pointed the library.
- Not here, deliberately: `zlib-stream` compression and gateway extensions,
  subprotocols, automatic sharding across many connections, message attachment
  upload (there is no `multipart/form-data` in v1: `MISSING-j2Wka`), scheduled
  events, voice, and the audit-log reason as a named parameter (push the header
  with `with_header` instead).
- `Interaction` owns a copy of its payload, so a handler can keep it; `on_event`
  is the uncloned payload. That is one deep copy per interaction.
