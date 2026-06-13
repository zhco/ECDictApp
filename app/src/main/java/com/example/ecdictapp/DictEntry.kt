package com.example.ecdictapp

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "dictionary")
data class DictEntry(
    @PrimaryKey val word: String,
    val phonetic: String = "",
    val definition: String = "",
    val translation: String = "",
    val pos: String = "",
    val collins: Int = 0,
    val oxford: Int = 0,
    val tag: String = "",
    val bnc: Int = 0,
    val frq: Int = 0,
    val exchange: String = "",
    val detail: String = "",
    val audio: String = ""
)
