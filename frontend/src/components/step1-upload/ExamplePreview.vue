<script setup>
// ============================================================================
// Props
// ============================================================================
defineProps({
  imageSrc: {
    type: String,
    default: '/dummy.png'
  }
})
</script>

<template>
  <!-- Equal-height side card matching PhotoDropzone height -->
  <aside
    aria-labelledby="example-preview-title"
    class="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"  >
    <!-- Card Heading -->
    <h2
      id="example-preview-title"
      class="text-[21px] font-bold leading-snug tracking-tight text-slate-900"
    >
      Example of a geometric preview
    </h2>

    <!-- Preview Image Container (loads /dummy.png by default) -->
    <div class="mt-5 overflow-hidden rounded-xl border border-slate-200/80 bg-slate-50">
      <img
        :src="imageSrc"
        alt="Example of a geometric wind turbine preview"
        class="aspect-[4/3] w-full object-cover"
      />
    </div>

    <!-- Disclaimer Caption -->
    <p class="mt-5 text-[14.5px] leading-relaxed text-slate-600">
      Not a photorealistic visualization. Buildings and trees may obstruct the actual view.
    </p>
  </aside>
</template>