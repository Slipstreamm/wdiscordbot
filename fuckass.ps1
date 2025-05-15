git log --author="Slipstream" --pretty=tformat: --numstat |
    ForEach-Object {
        $parts = $_ -split "`t"
        if ($parts.Count -ge 2) {
            $insertions += [int]$parts[0]
            $deletions += [int]$parts[1]
        }
    }
"Insertions: $insertions"
"Deletions: $deletions"