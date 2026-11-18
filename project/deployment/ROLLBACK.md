# Version 1.0 rollback

The Git tag `v1.0` preserves commit `2ec28dc`, before the opening animation.
It is backed up on GitHub. Database records and private environment files are
not part of this source snapshot.

For an immediate frontend rollback, select the Vercel deployment for commit
`2ec28dc` and promote it to production.

To remove the animation from source, revert the commit titled
`Add Karnataka opening sequence with accessible skip controls`, then push main.
Do not reset main or force-push; a revert preserves later work and history.

The intro plays once per browser tab session. To preview it again, open a new
session or remove `gaadamruta:intro:v3` from session storage. Reduced-motion
preferences bypass it entirely.
