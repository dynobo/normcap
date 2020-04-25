# How To Release new version

(Notes to myself)

## Prepare

1. Commit latest changes to `dev`, and see if tests run through
2. Increase version number (major.minor.patch):

```sh
bumpversion major
bumpversion minor
bumpversion patch
```

## Merge

1. Create pull request from master to dev
2. See, if all tests ran through
