<?php
session_start();

// === Login & Authentication ===
// Only proceed if the current session is authenticated.
// If not, show a login form.
if (!isset($_SESSION['logged_in'])) {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['username'], $_POST['password'])) {
        $user_env = getenv('user'); // environment variable "user"
        $pass_env = getenv('pass'); // environment variable "pass"
        if ($_POST['username'] === $user_env && $_POST['password'] === $pass_env) {
            $_SESSION['logged_in'] = true;
            header("Location: index.php");
            exit;
        } else {
            $error = "Invalid credentials.";
        }
    }
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f0f0f0;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
            }
            .login-container {
                background: #fff;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                width: 300px;
            }
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 8px;
                margin: 5px 0 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            input[type="submit"] {
                background: #007BFF;
                color: white;
                border: none;
                padding: 10px;
                width: 100%;
                cursor: pointer;
                border-radius: 3px;
            }
            input[type="submit"]:hover {
                background: #0056b3;
            }
            .error {
                color: red;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>Login</h2>
            <?php if(isset($error)) echo "<p class='error'>{$error}</p>"; ?>
            <form method="POST">
                <label>Username</label>
                <input type="text" name="username" required>
                <label>Password</label>
                <input type="password" name="password" required>
                <input type="submit" value="Login">
            </form>
        </div>
    </body>
    </html>
    <?php
    exit; // Do not execute the rest until logged in.
}

// === End Authentication ===

// Determine which action to do.
$action = "";
if (isset($_GET['action'])) {
    $action = $_GET['action'];
} elseif (isset($_POST['action'])) {
    $action = $_POST['action'];
}

$output = ""; // To hold any output from actions

// Handle the different actions.
switch ($action) {
    case "version":
        // Gets the current commit from /home/server/wdiscordbotserver.
        $botDir = '/home/server/wdiscordbotserver';
        if (is_dir($botDir)) {
            $cmd = 'cd ' . escapeshellarg($botDir) . ' && git rev-parse HEAD 2>&1';
            $output = shell_exec($cmd);
        } else {
            $output = "Directory not found.";
        }
        break;

    case "update":
        // Removes the folder and clones the repository anew.
        $botDir = '/home/server/wdiscordbotserver';
        if (is_dir($botDir)) {
            $rmCmd = 'rm -rf ' . escapeshellarg($botDir) . ' 2>&1';
            $output .= shell_exec($rmCmd);
        }
        $cloneCmd = 'git clone https://gitlab.com/pancakes1234/wdiscordbotserver.git ' . escapeshellarg($botDir) . ' 2>&1';
        $output .= shell_exec($cloneCmd);
        break;

    case "data":
        // If editing a file, process its content.
        if (isset($_GET['file'])) {
            $file = $_GET['file'];
            $baseDir = realpath('/home/server');
            $realFile = realpath($file);
            if ($realFile === false || strpos($realFile, $baseDir) !== 0) {
                $output = "Invalid file.";
            } else {
                if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['content'])) {
                    file_put_contents($realFile, $_POST['content']);
                    $output = "File updated successfully.";
                }
            }
        }
        break;

    // Other actions (such as terminal) will be handled in the UI below.
    default:
        // No action or unrecognized action.
        break;
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Discord Bot Admin API</title>
    <style>
        /* General styling */
        body {
            font-family: Arial, sans-serif;
            background: #e9e9e9;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: auto;
            background: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        header {
            margin-bottom: 20px;
        }
        header button {
            padding: 10px 20px;
            margin-right: 10px;
            border: none;
            background: #007BFF;
            color: white;
            cursor: pointer;
            border-radius: 3px;
        }
        header button:hover {
            background: #0056b3;
        }
        .output {
            background: #f4f4f4;
            padding: 10px;
            margin-top: 20px;
            white-space: pre-wrap;
        }
        .file-list {
            list-style-type: none;
            padding: 0;
        }
        .file-list li {
            margin: 5px 0;
        }
        a {
            text-decoration: none;
            color: #007BFF;
        }
        a:hover {
            text-decoration: underline;
        }
        textarea {
            width: 100%;
            height: 300px;
        }
        /* Terminal tabs styling */
        #terminal-tabs button {
            padding: 8px 16px;
            border: none;
            margin-right: 5px;
            background: #007BFF;
            color: white;
            border-radius: 3px;
            cursor: pointer;
        }
        #terminal-tabs button:hover {
            background: #0056b3;
        }
    </style>
    <script>
        // For Version and Update actions we can use fetch to load the result via AJAX.
        function doAction(action) {
            if (action === "data" || action === "terminal") {
                window.location.href = "?action=" + action;
            } else {
                fetch("?action=" + action)
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById("output").innerText = data;
                    });
            }
        }
        // SSH Connect functionality using the "ssh://" protocol.
        function doSSH() {
            var sshUser = "<?php echo getenv('user'); ?>"; // SSH username from the env.
            var sshHost = window.location.hostname; // use current hostname.
            window.location.href = "ssh://" + sshUser + "@" + sshHost;
        }
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Discord Bot Admin API</h1>
            <button onclick="doAction('version')">Version</button>
            <button onclick="doAction('update')">Update</button>
            <button onclick="window.location.href='?action=data'">Data</button>
            <button onclick="doSSH()">SSH Connect</button>
            <button onclick="window.location.href='?action=terminal'">Terminal</button>
        </header>
        <!-- Output area for AJAX-returned actions -->
        <div id="output" class="output"><?php echo htmlspecialchars($output); ?></div>

        <?php
        // === Data Section ===
        if ($action === "data") {
            if (!isset($_GET['file'])) {
                $baseDir = '/home/server';
                echo "<h2>Files in {$baseDir}</h2>";
                echo "<ul class='file-list'>";
                $iterator = new RecursiveIteratorIterator(
                    new RecursiveDirectoryIterator($baseDir, RecursiveDirectoryIterator::SKIP_DOTS)
                );
                foreach ($iterator as $fileInfo) {
                    $filePath = $fileInfo->getPathname();
                    echo "<li><a href='?action=data&file=" . urlencode($filePath) . "'>" . htmlspecialchars($filePath) . "</a></li>";
                }
                echo "</ul>";
            } else {
                $file = $_GET['file'];
                $baseDir = realpath('/home/server');
                $realFile = realpath($file);
                if ($realFile === false || strpos($realFile, $baseDir) !== 0) {
                    echo "<p>Invalid file.</p>";
                } else {
                    echo "<h2>Editing: " . htmlspecialchars($realFile) . "</h2>";
                    echo "<form method='POST' action='?action=data&file=" . urlencode($realFile) . "'>";
                    echo "<textarea name='content'>" . htmlspecialchars(file_get_contents($realFile)) . "</textarea><br>";
                    echo "<input type='hidden' name='action' value='data'>";
                    echo "<input type='submit' value='Save' style='padding:10px 20px; margin-top:10px;'>";
                    echo "</form>";
                }
            }
        }
        // === Terminal Section ===
        elseif ($action === "terminal") :
            // This section provides two terminal options:
            // 1. Wetty Terminal via an iframe (assumes Wetty is running on port 3000)
            // 2. A direct integration of xterm.js (which connects via WebSocket to a Node.js pty server on port 3001)
        ?>
            <div id="terminal-tabs" style="margin-bottom:10px;">
                <button onclick="showTab('wetty')">Wetty Terminal</button>
                <button onclick="showTab('xterm')">Xterm Terminal</button>
            </div>
            <div id="wetty" class="terminal-tab" style="display:block;">
                <h2>Wetty Terminal</h2>
                <iframe src="http://<?php echo $_SERVER['HTTP_HOST']; ?>:3000" width="100%" height="500px" frameborder="0"></iframe>
            </div>
            <div id="xterm" class="terminal-tab" style="display:none;">
                <h2>Xterm Terminal</h2>
                <div id="xterm-container" style="width: 100%; height: 500px;"></div>
            </div>
            <!-- Load xterm.js resources -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm/css/xterm.css" />
            <script src="https://cdn.jsdelivr.net/npm/xterm/lib/xterm.js"></script>
            <script>
                function showTab(tab) {
                    document.getElementById('wetty').style.display = (tab === 'wetty') ? 'block' : 'none';
                    document.getElementById('xterm').style.display = (tab === 'xterm') ? 'block' : 'none';
                }
                // Initialize xterm.js for the Xterm Terminal.
                // NOTE: You MUST run a WebSocket Node.js server (for example, using node-pty and ws)
                // listening on port 3001 to support this connection.
                window.addEventListener('load', function() {
                    // Initialize the terminal only once.
                    const terminal = new Terminal();
                    terminal.open(document.getElementById('xterm-container'));
                    
                    const socket = new WebSocket('ws://<?php echo $_SERVER['HTTP_HOST']; ?>:3001');
                    socket.onopen = function() {
                        terminal.write("Connected to shell\r\n");
                    };
                    terminal.onData(function(data) {
                        socket.send(data);
                    });
                    socket.onmessage = function(event) {
                        terminal.write(event.data);
                    };
                    socket.onerror = function() {
                        terminal.write("\r\nError connecting to shell.\r\n");
                    };
                    socket.onclose = function() {
                        terminal.write("\r\nConnection closed.\r\n");
                    };
                });
            </script>
        <?php
        endif;
        ?>
    </div>
</body>
</html>
