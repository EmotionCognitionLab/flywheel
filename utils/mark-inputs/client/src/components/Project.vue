<template>
    <router-link
    class="text-medium, clickable-row"
    tag="li"
    :to="{ name: 'project', params: { id: project.id }}">
    {{ project.label }}
    </router-link>
</template>

<script>
export default {
    props: {
        project: {
            type: Object,
            required: true
        }
    }
}
</script>

<style>
    li {
        border: 1px solid #eff1f5;
        padding: 10px;
        max-width: 300px;
    }

    .text-medium {
        color: #5871a2;
    }
</style>