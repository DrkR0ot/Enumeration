#!/bin/bash

# === Configuration ===
echo -n "Enter your username: "
read -r USER
echo -n "Enter your password: "
read -r PASSWORD
echo ""

echo -n "Enter the server IP address: "
read -r SERVER_IP

RID_FILE='rid_users.txt'
USER_LIST_FILE='list_dom_users.txt'

# Check RPC connection
echo "[*] Checking connection to $SERVER_IP..."
rpcclient --user="$USER%$PASSWORD" "$SERVER_IP" -c 'exit' &>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Failed to connect to $SERVER_IP with user $USER. Please check credentials and access."
    exit 1
fi

echo "[+] Successfully connected to $SERVER_IP"

# Step 1: Retrieve group list and their RIDs
echo "[*] Retrieving groups..."
rpcclient --user="$USER%$PASSWORD" "$SERVER_IP" -c 'enumdomgroups' > groups_list.txt

if [ ! -s groups_list.txt ]; then
    echo "[!] Failed to retrieve groups. Check the user's permissions."
    exit 1
fi

cat groups_list.txt
echo "[*] Select a group from the list above (enter the RID): "
read -r GROUP_RID

if [ -z "$GROUP_RID" ]; then
    echo "[!] No group selected."
    exit 1
fi

echo "[+] Selected group with RID: $GROUP_RID"

# Step 2: Extract user RIDs from the selected group
echo "[*] Retrieving group members..."
rpcclient --user="$USER%$PASSWORD" "$SERVER_IP" -c "querygroupmem $GROUP_RID" | awk -F'[][]' '{print $2}' > "$RID_FILE"

echo "[+] User RIDs saved to $RID_FILE"

# Check if RID file contains data
if [ ! -s "$RID_FILE" ]; then
    echo "[!] No users found in this group."
    exit 1
fi

# Step 3: Retrieve usernames from RIDs
echo "[*] Retrieving usernames..."
> "$USER_LIST_FILE"  # Clear output file

while IFS= read -r RID; do
    if [ -n "$RID" ]; then
        USERNAME=$(rpcclient --user="$USER%$PASSWORD" "$SERVER_IP" -c "queryuser $RID" | grep "User Name" | awk -F'[:[:space:]]+' '{print $4}')
        if [ -n "$USERNAME" ]; then
            echo "$USERNAME" >> "$USER_LIST_FILE"
        fi
    fi
done < "$RID_FILE"

echo "[+] User list saved to $USER_LIST_FILE"

# Display the result
echo "=== Found Users ==="
cat "$USER_LIST_FILE"
