# Desktop notification when a command that ran for a long time finishes.
# Installed to ~/.config/bash/ and sourced from ~/.bashrc by restore.sh.
# Settings (set before sourcing to override):
#   LONGCMD_NOTIFY_SECS    minimum run time in seconds (default 60)
#   LONGCMD_NOTIFY_IGNORE  programs you sit inside, whose exit is not news

[[ $- == *i* ]] || return 0
command -v notify-send >/dev/null || return 0

: "${LONGCMD_NOTIFY_SECS:=60}"
: "${LONGCMD_NOTIFY_IGNORE:=claude codex grok ssh vim vi nano less more man top htop btop watch mpv tmux screen ipython}"

__lcn_armed=
__lcn_start=
__lcn_cmd=
__lcn_histn=
__lcn_saved=

# DEBUG trap, runs before every command. Only the first command after a
# prompt starts the clock; __lcn_arm (last PROMPT_COMMAND entry) re-arms it.
# Tab completion also fires the trap, so it is skipped (COMP_LINE is set).
__lcn_preexec() {
    [[ -n $__lcn_armed && -z ${COMP_LINE-} ]] || return 0
    __lcn_armed=
    __lcn_start=$EPOCHSECONDS
    __lcn_cmd=$BASH_COMMAND
    # HISTCMD still equals its value at the prompt only if this line was
    # saved to history (not a leading-space or duplicate line)
    __lcn_saved=$(( HISTCMD == __lcn_histn ))
}

# First PROMPT_COMMAND entry, so $? is still the command's exit status
__lcn_precmd() {
    local status=$?
    [[ -n $__lcn_start ]] || return $status
    local secs=$(( EPOCHSECONDS - __lcn_start ))
    __lcn_start=
    # 130 = Ctrl+C, 148 = Ctrl+Z: you were at the terminal anyway
    if (( secs >= LONGCMD_NOTIFY_SECS && status != 130 && status != 148 )); then
        local prog=${__lcn_cmd%% *}
        prog=${prog##*/}
        if [[ " $LONGCMD_NOTIFY_IGNORE " != *" $prog "* ]]; then
            # Full line from history. An unsaved line is either a duplicate
            # (history has the same text) or hidden by a leading space (it
            # does not); then only the first simple command is known.
            local line
            line=$(HISTTIMEFORMAT= history 1 | sed -E 's/^ *[0-9]+\*? *//')
            (( __lcn_saved )) || [[ $line == "$__lcn_cmd"* ]] || line=$__lcn_cmd
            local took
            if (( secs >= 3600 )); then
                printf -v took '%dh %02dm' $((secs / 3600)) $((secs % 3600 / 60))
            else
                printf -v took '%dm %02ds' $((secs / 60)) $((secs % 60))
            fi
            local title icon
            if (( status == 0 )); then
                title="Done after $took"; icon=utilities-terminal
            else
                title="Failed (exit $status) after $took"; icon=dialog-error
            fi
            (notify-send -a Terminal -i "$icon" "$title" "${line:0:200}"$'\n'"${PWD/#$HOME/\~}" &)
        fi
    fi
    return $status
}

__lcn_arm() { __lcn_armed=1; __lcn_histn=$HISTCMD; }

trap '__lcn_preexec' DEBUG
# Array form (bash 5.1+) keeps entries added by others, e.g. VTE's __vte_osc7;
# the guard stops a re-sourced ~/.bashrc from adding the hooks twice
[[ " ${PROMPT_COMMAND[*]} " == *" __lcn_precmd "* ]] ||
    PROMPT_COMMAND=(__lcn_precmd "${PROMPT_COMMAND[@]}" __lcn_arm)
__lcn_arm
