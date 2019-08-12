<template>
    <tr 
    class="clickable-row " 
    :class="{ selected: isSelected }"
    :data-sessid="session['id']"
    :data-subjlabel="session['subject_label']"
    >
        <td>{{ session['subject_label'] }}</td>
        <td>{{ session['label'] }}</td>
    </tr>
</template>

<script>
export default {
    props: {
        session: {
            type: Object,
            required: true
        },
        isSelected: {
            type: Boolean,
            required: false,
            default: false
        }
    },
    watch: {
        isSelected: function(newVal, oldVal) {
            if (newVal) { // only run when isSelected is true
                document.querySelector(`[data-sessid="${this.session['id']}"]`).scrollIntoView()
            }
        }
    }
}
</script>

<style>
    tr.selected {
        background-color: aliceblue;
    }
</style>
