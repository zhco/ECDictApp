package com.example.ecdictapp

import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.io.File
import java.io.FileOutputStream

class AppDatabase private constructor(context: Context) : SQLiteOpenHelper(
    context, DB_NAME, null, DB_VERSION
) {

    val dao: DictDao = DictDaoImpl(writableDatabase)

    init {
        copyDatabaseIfNeeded(context)
    }

    private fun copyDatabaseIfNeeded(context: Context) {
        val dbFile = context.getDatabasePath(DB_NAME)
        if (dbFile.exists()) return

        dbFile.parentFile?.mkdirs()

        // Try to copy from assets
        try {
            context.assets.open("databases/$DB_NAME").use { input ->
                FileOutputStream(dbFile).use { output ->
                    input.copyTo(output)
                }
            }
        } catch (_: Exception) {
            // No prebuilt database in assets, will create empty
        }
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS dictionary (
                word TEXT PRIMARY KEY,
                phonetic TEXT,
                definition TEXT,
                translation TEXT,
                pos TEXT,
                collins INTEGER,
                oxford INTEGER,
                tag TEXT,
                bnc INTEGER,
                frq INTEGER,
                exchange TEXT,
                detail TEXT,
                audio TEXT
            )
            """.trimIndent()
        )
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // No migration needed for v1
    }

    companion object {
        private const val DB_NAME = "ecdict.db"
        private const val DB_VERSION = 1

        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = AppDatabase(context.applicationContext)
                INSTANCE = instance
                instance
            }
        }
    }

    private class DictDaoImpl(private val db: SQLiteDatabase) : DictDao {

        override suspend fun lookup(word: String): DictEntry? {
            return db.rawQuery(
                "SELECT * FROM dictionary WHERE word = ? LIMIT 1",
                arrayOf(word)
            ).use { cursor ->
                if (cursor.moveToFirst()) cursor.toDictEntry() else null
            }
        }

        override fun lookupFlow(word: String): Flow<DictEntry?> = flow {
            emit(lookup(word))
        }

        override suspend fun searchPrefix(prefix: String, limit: Int): List<SearchResult> {
            return db.rawQuery(
                "SELECT word, translation FROM dictionary WHERE word LIKE ? || '%' ORDER BY word LIMIT ?",
                arrayOf(prefix, limit.toString())
            ).use { cursor ->
                val results = mutableListOf<SearchResult>()
                while (cursor.moveToNext()) {
                    results.add(
                        SearchResult(
                            word = cursor.getString(cursor.getColumnIndexOrThrow("word")),
                            translation = cursor.getString(cursor.getColumnIndexOrThrow("translation")) ?: ""
                        )
                    )
                }
                results
            }
        }

        override fun searchPrefixFlow(prefix: String, limit: Int): Flow<List<SearchResult>> = flow {
            emit(searchPrefix(prefix, limit))
        }

        override suspend fun count(): Int {
            return db.rawQuery("SELECT COUNT(*) FROM dictionary", null).use { cursor ->
                if (cursor.moveToFirst()) cursor.getInt(0) else 0
            }
        }

        private fun Cursor.toDictEntry(): DictEntry {
            return DictEntry(
                word = getString(getColumnIndexOrThrow("word")),
                phonetic = getString(getColumnIndexOrThrow("phonetic")) ?: "",
                definition = getString(getColumnIndexOrThrow("definition")) ?: "",
                translation = getString(getColumnIndexOrThrow("translation")) ?: "",
                pos = getString(getColumnIndexOrThrow("pos")) ?: "",
                collins = getInt(getColumnIndexOrThrow("collins")),
                oxford = getInt(getColumnIndexOrThrow("oxford")),
                tag = getString(getColumnIndexOrThrow("tag")) ?: "",
                bnc = getInt(getColumnIndexOrThrow("bnc")),
                frq = getInt(getColumnIndexOrThrow("frq")),
                exchange = getString(getColumnIndexOrThrow("exchange")) ?: "",
                detail = getString(getColumnIndexOrThrow("detail")) ?: "",
                audio = getString(getColumnIndexOrThrow("audio")) ?: ""
            )
        }
    }
}
