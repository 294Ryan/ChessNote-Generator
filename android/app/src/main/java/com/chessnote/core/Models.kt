package com.chessnote.core

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

fun newId(): String = UUID.randomUUID().toString()

private fun JSONObject.strOrNull(key: String): String? = if (!has(key) || isNull(key)) null else getString(key)

private fun JSONObject.putNullable(key: String, value: String?) {
    put(key, value ?: JSONObject.NULL)    // org.json put(key, null) removes the field; use NULL
}

private fun <T> JSONArray.toList(parse: (JSONObject) -> T): MutableList<T> {
    val list = mutableListOf<T>()
    for (i in 0 until length()) {
        list.add(parse(getJSONObject(i)))
    }
    return list
}

class Line(var pgn: String = "", var imagePath: String? = null, var noImage: Boolean = false) {
    var id: String = newId()
    var imageData: String? = null    // Mobile only: base64 of the uploaded image; ignored by desktop when loading

    fun toJson() = JSONObject().apply {
        put("id", id)
        put("pgn", pgn)
        putNullable("imagePath", imagePath)    // Desktop path preserved as-is so round-trips don't lose it
        put("noImage", noImage)
        imageData?.let { put("imageData", it) }
    }

    companion object {
        fun fromJson(o: JSONObject) = Line(o.getString("pgn"), o.strOrNull("imagePath"), o.optBoolean("noImage", false)).apply {
            id = o.getString("id")
            imageData = o.strOrNull("imageData")
        }
    }
}

class SubCategory(var name: String = "", var description: String = "") {
    var id: String = newId()
    val lines = mutableListOf<Line>()

    fun toJson() = JSONObject().apply {
        put("id", id)
        put("name", name)
        put("description", description)
        put("lines", JSONArray(lines.map { it.toJson() }))
    }

    companion object {
        fun fromJson(o: JSONObject) = SubCategory(o.getString("name"), o.optString("description", "")).apply {
            id = o.getString("id")
            lines.addAll(o.getJSONArray("lines").toList(Line::fromJson))
        }
    }
}

class Variant(var name: String = "", var description: String = "") {
    var id: String = newId()
    val subCategories = mutableListOf<SubCategory>()
    val lines = mutableListOf<Line>()

    fun toJson() = JSONObject().apply {
        put("id", id)
        put("name", name)
        put("description", description)
        put("subCategories", JSONArray(subCategories.map { it.toJson() }))
        put("lines", JSONArray(lines.map { it.toJson() }))
    }

    companion object {
        fun fromJson(o: JSONObject) = Variant(o.getString("name"), o.optString("description", "")).apply {
            id = o.getString("id")
            subCategories.addAll(o.getJSONArray("subCategories").toList(SubCategory::fromJson))
            lines.addAll(o.getJSONArray("lines").toList(Line::fromJson))
        }
    }
}

class Opening(var name: String = "", var description: String = "", var startingPgn: String = "") {
    var startingImagePath: String? = null
    var startingImageData: String? = null    // Mobile only, same as Line.imageData
    var startingNoImage = false
    var orientation = "white"    // white / black
    val variants = mutableListOf<Variant>()

    fun toJson() = JSONObject().apply {
        put("name", name)
        put("description", description)
        put("startingPgn", startingPgn)
        putNullable("startingImagePath", startingImagePath)
        put("startingNoImage", startingNoImage)
        put("orientation", orientation)
        put("variants", JSONArray(variants.map { it.toJson() }))
        startingImageData?.let { put("startingImageData", it) }
    }

    companion object {
        fun fromJson(o: JSONObject) = Opening(o.getString("name"), o.getString("description"), o.getString("startingPgn")).apply {
            startingImagePath = o.strOrNull("startingImagePath")
            startingImageData = o.strOrNull("startingImageData")
            startingNoImage = o.optBoolean("startingNoImage", false)
            orientation = o.optString("orientation", "white")
            variants.addAll(o.getJSONArray("variants").toList(Variant::fromJson))
        }

        fun parse(text: String) = fromJson(JSONObject(text))
    }
}
