# Legal compliance and privacy

This document tracks Riot Games policy requirements and privacy guarantees for Pool Ensemble. Verify the latest Riot Developer Portal policies before public launch.

## Riot Games legal notice

The following disclaimer must remain visible in the web application footer and in `README.md` / `README.pt-BR.md`:

> Pool Ensemble isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

Legal Jibber Jabber notice:

> Pool Ensemble was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.

## Product restrictions

- Do not register or imply any official affiliation with Riot Games or League of Legends.
- Register the product in the Riot Developer Portal before public announcement.
- Never compute, display, or approximate MMR, ELO, skill ratings, or ranked alternatives. Only champion mastery weights and playstyle archetypes are presented.
- Keep donation links out of rendered share cards; review current Legal Jibber Jabber terms before enabling any support link on the site or repository.
- Respect personal API key rate limits (`20 req/s` and `100 req/2 min`) with global rate limiting and caching. If traffic requires a production API key later, add formal Terms of Service and Privacy Policy pages prior to applying.

## Data minimization and privacy

- Only store the minimum state needed for sharing and aggregate statistics: short result `id`, `region`, weighted `pool`, classified `archetype`, and `created_at` timestamp.
- Store PUUIDs only as salted cryptographic hashes for deduplication and cache lookups; never persist raw PUUIDs.
- Never persist client IP addresses in logs or Redis storage.
- Allow players to hide their summoner name on rendered cards.
- Provide a public removal route so anyone with a share link can delete a stored result before its TTL expires.
