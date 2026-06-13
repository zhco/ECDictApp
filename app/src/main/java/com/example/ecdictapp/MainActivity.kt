package com.example.ecdictapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.ecdictapp.ui.components.DictSearchBar
import com.example.ecdictapp.ui.components.SuggestionList
import com.example.ecdictapp.ui.components.WordDetailScreen
import com.example.ecdictapp.ui.theme.ECDictTheme

class MainActivity : ComponentActivity() {

    private val database by lazy { AppDatabase.getDatabase(this) }
    private val viewModel: DictViewModel by viewModels {
        DictViewModel.Factory(DictRepository(database.dao))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ECDictTheme {
                MainScreen(viewModel)
            }
        }
    }
}

@Composable
fun MainScreen(viewModel: DictViewModel) {
    val searchQuery by viewModel.searchQuery.collectAsState()
    val searchResults by viewModel.searchResults.collectAsState()
    val selectedWord by viewModel.selectedWord.collectAsState()
    val selectedEntry by viewModel.selectedEntry.collectAsState()

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        if (selectedEntry != null) {
            WordDetailScreen(
                entry = selectedEntry!!,
                onBack = { viewModel.clearSelection() }
            )
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp)
            ) {
                // 标题
                Text(
                    text = "ECDict 离线词典",
                    style = MaterialTheme.typography.headlineMedium,
                    modifier = Modifier.padding(bottom = 16.dp)
                )

                // 搜索栏
                DictSearchBar(
                    query = searchQuery,
                    onQueryChange = { viewModel.onSearchQueryChange(it) },
                    onClear = { viewModel.onSearchQueryChange("") }
                )

                Spacer(modifier = Modifier.height(8.dp))

                // 搜索结果
                if (searchResults.isEmpty() && searchQuery.isNotBlank()) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "未找到匹配的单词",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                } else if (searchQuery.isBlank()) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "输入单词开始查询",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                } else {
                    SuggestionList(
                        results = searchResults,
                        onWordSelected = { viewModel.onWordSelected(it) }
                    )
                }
            }
        }
    }
}
