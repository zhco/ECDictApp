package com.example.ecdictapp.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ecdictapp.DictEntry

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WordDetailScreen(
    entry: DictEntry,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(entry.word) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        },
        modifier = modifier
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // 单词标题和音标
            WordHeader(entry)

            // 词性
            if (entry.pos.isNotBlank()) {
                PosChips(entry.pos)
            }

            // 标签（考试标签）
            if (entry.tag.isNotBlank()) {
                TagChips(entry.tag)
            }

            // 中文释义
            if (entry.translation.isNotBlank()) {
                TranslationCard(entry.translation)
            }

            // 英文释义
            if (entry.definition.isNotBlank()) {
                DefinitionCard(entry.definition)
            }

            // 词形变化
            if (entry.exchange.isNotBlank()) {
                ExchangeCard(entry.exchange)
            }

            // 柯林斯/牛津标识
            if (entry.collins > 0 || entry.oxford > 0) {
                RatingInfo(entry.collins, entry.oxford)
            }
        }
    }
}

@Composable
private fun WordHeader(entry: DictEntry) {
    Column {
        Text(
            text = entry.word,
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Bold
        )
        if (entry.phonetic.isNotBlank()) {
            Text(
                text = entry.phonetic,
                style = MaterialTheme.typography.titleMedium,
                fontStyle = FontStyle.Italic,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun PosChips(pos: String) {
    val posList = pos.split("/").filter { it.isNotBlank() }
    if (posList.isNotEmpty()) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            posList.forEach { p ->
                SuggestionChip(
                    label = { Text(p.trim()) },
                    onClick = {}
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TagChips(tag: String) {
    val tagList = tag.split(" ").filter { it.isNotBlank() }
    if (tagList.isNotEmpty()) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            tagList.forEach { t ->
                val label = when (t.trim()) {
                    "zk" -> "中考"
                    "gk" -> "高考"
                    "cet4" -> "四级"
                    "cet6" -> "六级"
                    "ky" -> "考研"
                    "ielts" -> "雅思"
                    "toefl" -> "托福"
                    "gre" -> "GRE"
                    else -> t.trim()
                }
                FilterChip(
                    selected = true,
                    label = { Text(label) },
                    onClick = {},
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = MaterialTheme.colorScheme.tertiaryContainer,
                        selectedLabelColor = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                )
            }
        }
    }
}

@Composable
private fun TranslationCard(translation: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "中文释义",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            translation.lines().forEach { line ->
                if (line.isNotBlank()) {
                    Text(
                        text = line,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.padding(vertical = 2.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun DefinitionCard(definition: String) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "English Definition",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.secondary,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            definition.lines().forEach { line ->
                if (line.isNotBlank()) {
                    Text(
                        text = line,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(vertical = 2.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun ExchangeCard(exchange: String) {
    val exchanges = exchange.split("/").filter { it.isNotBlank() }
    if (exchanges.isNotEmpty()) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "词形变化",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                exchanges.forEach { ex ->
                    val parts = ex.split(":", limit = 2)
                    if (parts.size == 2) {
                        val label = when (parts[0]) {
                            "p" -> "过去式"
                            "d" -> "过去分词"
                            "i" -> "现在分词"
                            "3" -> "第三人称"
                            "r" -> "比较级"
                            "t" -> "最高级"
                            "s" -> "复数"
                            "0" -> "原形"
                            "1" -> "变换形式"
                            else -> parts[0]
                        }
                        Row(
                            modifier = Modifier.padding(vertical = 2.dp)
                        ) {
                            Text(
                                text = "$label: ",
                                fontWeight = FontWeight.Medium,
                                style = MaterialTheme.typography.bodyMedium
                            )
                            Text(
                                text = parts[1],
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun RatingInfo(collins: Int, oxford: Int) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (collins > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Star,
                    contentDescription = "柯林斯星级",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    text = "柯林斯 $collins 星",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
        if (oxford > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.School,
                    contentDescription = "牛津3000",
                    tint = MaterialTheme.colorScheme.secondary,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    text = "牛津 3000 核心词汇",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.secondary
                )
            }
        }
    }
}
